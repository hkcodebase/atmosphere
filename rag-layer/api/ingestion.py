import hashlib
import os
from pathlib import Path
from typing import Generator

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredExcelLoader,
    UnstructuredMarkdownLoader,
)
from langchain_core.documents import Document

from config import settings
from db import get_embeddings, get_raw_driver

SUPPORTED_EXTENSIONS = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": TextLoader,
    ".md": UnstructuredMarkdownLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".xls": UnstructuredExcelLoader,
}


def _file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_file(path: str) -> list[Document]:
    ext = Path(path).suffix.lower()
    loader_cls = SUPPORTED_EXTENSIONS.get(ext)
    if not loader_cls:
        raise ValueError(f"Unsupported file type: {ext}")
    return loader_cls(path).load()


def chunk_documents(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    return splitter.split_documents(docs)


def _doc_id(path: str) -> str:
    return hashlib.sha256(path.encode()).hexdigest()


def _chunk_id(doc_id: str, index: int) -> str:
    return hashlib.sha256(f"{doc_id}:{index}".encode()).hexdigest()


def ingest_file(file_path: str) -> dict:
    """Ingest a single file into Neo4j. Returns status info."""
    path = Path(file_path)
    doc_id = _doc_id(str(path))
    file_hash = _file_hash(file_path)

    driver = get_raw_driver()
    with driver.session() as session:
        existing = session.run(
            "MATCH (d:Document {id: $id}) RETURN d.hash AS hash",
            id=doc_id,
        ).single()

        if existing and existing["hash"] == file_hash:
            driver.close()
            return {"status": "skipped", "reason": "unchanged", "path": file_path}

        # Remove stale chunks if file changed
        if existing:
            session.run(
                "MATCH (d:Document {id: $id})-[:HAS_CHUNK]->(c:Chunk) DETACH DELETE c",
                id=doc_id,
            )

    raw_docs = load_file(file_path)
    chunks = chunk_documents(raw_docs)
    embeddings = get_embeddings()

    texts = [c.page_content for c in chunks]
    vectors = embeddings.embed_documents(texts)

    with driver.session() as session:
        session.run(
            """
            MERGE (d:Document {id: $id})
            SET d.path = $path, d.name = $name, d.hash = $hash,
                d.chunk_count = $chunk_count
            """,
            id=doc_id,
            path=str(path),
            name=path.name,
            hash=file_hash,
            chunk_count=len(chunks),
        )
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            chunk_id = _chunk_id(doc_id, i)
            session.run(
                """
                MERGE (c:Chunk {id: $id})
                SET c.text = $text,
                    c.embedding = $embedding,
                    c.source = $source,
                    c.chunk_index = $index,
                    c.page = $page
                WITH c
                MATCH (d:Document {id: $doc_id})
                MERGE (d)-[:HAS_CHUNK]->(c)
                """,
                id=chunk_id,
                text=chunk.page_content,
                embedding=vector,
                source=str(path),
                index=i,
                page=chunk.metadata.get("page", 0),
                doc_id=doc_id,
            )

    driver.close()
    return {
        "status": "ingested",
        "path": file_path,
        "chunks": len(chunks),
    }


def scan_and_ingest(docs_path: str) -> Generator[dict, None, None]:
    """Walk docs_path and ingest all supported files."""
    root = Path(docs_path)
    for file_path in root.rglob("*"):
        if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                yield ingest_file(str(file_path))
            except Exception as e:
                yield {"status": "error", "path": str(file_path), "error": str(e)}
