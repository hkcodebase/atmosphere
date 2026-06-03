import os
import shutil
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import settings
from db import init_schema, get_raw_driver
from ingestion import ingest_file, scan_and_ingest, SUPPORTED_EXTENSIONS
from rag import rag_query, similarity_search


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_schema()
    yield


app = FastAPI(title="RAG API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ────────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


# ── Documents ─────────────────────────────────────────────────────────────────

@app.get("/documents")
def list_documents():
    driver = get_raw_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (d:Document) RETURN d.id AS id, d.name AS name, "
            "d.path AS path, d.chunk_count AS chunks"
        )
        docs = [dict(r) for r in result]
    driver.close()
    return {"documents": docs, "total": len(docs)}


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    driver = get_raw_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (d:Document {id: $id}) RETURN d.name AS name", id=doc_id
        ).single()
        if not result:
            raise HTTPException(status_code=404, detail="Document not found")
        session.run(
            "MATCH (d:Document {id: $id})-[:HAS_CHUNK]->(c:Chunk) DETACH DELETE c, d",
            id=doc_id,
        )
    driver.close()
    return {"deleted": doc_id}


# ── Upload ────────────────────────────────────────────────────────────────────

@app.post("/ingest/upload")
async def upload_and_ingest(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type {ext}. Supported: {list(SUPPORTED_EXTENSIONS)}",
        )
    tmp_path = f"/tmp/{file.filename}"
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    result = ingest_file(tmp_path)
    os.unlink(tmp_path)
    return result


@app.post("/ingest/scan")
def ingest_scan():
    """Scan the mounted /docs folder and ingest all supported files (streaming)."""
    def generate():
        import json
        for result in scan_and_ingest(settings.docs_path):
            yield json.dumps(result) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


# ── Search & RAG ──────────────────────────────────────────────────────────────

@app.post("/search")
def search(req: SearchRequest):
    hits = similarity_search(req.query, top_k=req.top_k)
    return {"query": req.query, "results": hits}


@app.post("/query")
def query(req: QueryRequest):
    result = rag_query(req.question, top_k=req.top_k)
    return result


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.get("/stats")
def stats():
    driver = get_raw_driver()
    with driver.session() as session:
        doc_count = session.run("MATCH (d:Document) RETURN count(d) AS n").single()["n"]
        chunk_count = session.run("MATCH (c:Chunk) RETURN count(c) AS n").single()["n"]
    driver.close()
    return {"documents": doc_count, "chunks": chunk_count}
