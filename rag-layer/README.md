# RAG Layer — Local Document Search with Gemma + Neo4j

A fully local RAG (Retrieval-Augmented Generation) system:

| Service | Description | Port |
|---------|-------------|------|
| **Gemma** | llama.cpp server serving a GGUF model | 8080 |
| **Neo4j** | Graph DB + vector index | 7474 (browser), 7687 (bolt) |
| **API** | FastAPI + LangChain RAG pipeline | 8000 |
| **UI** | React SPA | 3000 |

---

## 1. Download a Gemma GGUF model

Gemma 3 4B (recommended for CPU):
```
https://huggingface.co/google/gemma-3-4b-it-qat-q4_0-gguf
```
Place the `.gguf` file in the `models/` folder (or anywhere — point `MODELS_FOLDER` at it).

## 2. Configure `.env`

```bash
cp .env.example .env
```

Edit `.env`:
```env
# Folder containing your documents
DOCS_FOLDER=C:/Users/you/Documents

# Folder containing the GGUF model file
MODELS_FOLDER=./models

# The filename of your GGUF file
GEMMA_MODEL_FILE=gemma-3-4b-it-q4_0.gguf
```

## 3. Start everything

```bash
docker compose up --build
```

First run builds the API image (downloads embedding model) — takes a few minutes.

## 4. Use it

| URL | What |
|-----|------|
| http://localhost:3000 | UI |
| http://localhost:8000/docs | API Swagger |
| http://localhost:7474 | Neo4j Browser |

### Ingest your documents
1. Open http://localhost:3000
2. Go to **Ingest** tab
3. Either drag-drop individual files, or click **Scan & Ingest All** to process everything in `DOCS_FOLDER`

### Ask questions
Go to **Ask** tab, type a question — Gemma answers using your documents.

### Semantic search
Go to **Search** tab for raw similarity search without LLM generation.

---

## GPU acceleration

Uncomment the `deploy.resources` block in `docker-compose.yml` under the `gemma` service to enable NVIDIA GPU passthrough.

## Changing the model

Point `GEMMA_MODEL_FILE` at any GGUF model file (Mistral, Llama, Phi, etc.) — the llama.cpp server is model-agnostic.
