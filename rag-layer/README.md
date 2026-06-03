# RAG Layer — Local Document Search with Gemma + Neo4j

A fully local RAG (Retrieval-Augmented Generation) system powered by **Docker Model Runner**.

| Service | Description | Port |
|---------|-------------|------|
| **llm** | Docker Model Runner (Gemma via `docker model run`) | internal |
| **Neo4j** | Graph DB + vector index | 7474 (browser), 7687 (bolt) |
| **API** | FastAPI + LangChain RAG pipeline | 8000 |
| **UI** | React SPA | 3000 |

---

## Prerequisites

- **Docker Desktop 4.40+** with **Docker Model Runner** enabled
  - Settings → Features in development → Docker Model Runner ✓

---

## 1. Configure `.env`

```bash
cp .env.example .env
```

Edit `.env`:
```env
# Your local documents folder
DOCS_FOLDER=C:/Users/you/Documents

# Model from Docker Hub AI catalog
GEMMA_MODEL=ai/gemma3:4B-Q4_K_M
```

The model is downloaded automatically on first `docker compose up`.
To pre-pull it manually:
```bash
docker model pull ai/gemma3:4B-Q4_K_M
```

Browse all available models:
```bash
docker model list
```

## 2. Start everything

```bash
docker compose up --build
```

First run builds the API image (downloads embedding model) and pulls the LLM — takes a few minutes.

## 3. Use it

| URL | What |
|-----|------|
| http://localhost:3000 | UI |
| http://localhost:8000/docs | API Swagger |
| http://localhost:7474 | Neo4j Browser (neo4j / rag_password) |

### Ingest your documents
1. Open http://localhost:3000
2. Go to **Ingest** tab
3. Drag-drop files, or click **Scan & Ingest All** to process everything in `DOCS_FOLDER`

Supported formats: **PDF, DOCX, TXT, MD, XLSX, XLS**

### Ask questions
**Ask** tab — Gemma answers using your documents as context.

### Semantic search
**Search** tab — raw similarity search without LLM generation.

---

## How Docker Model Runner works

Docker Model Runner runs models natively on your machine (CPU or GPU) and exposes an OpenAI-compatible API inside the Docker network at:

```
http://model-runner.docker.internal/engines/llama.cpp/v1
```

No Ollama, no llama.cpp containers, no model files to manage manually.

## Changing the model

Edit `GEMMA_MODEL` in `.env` to any model from the Docker Hub AI catalog:

```env
GEMMA_MODEL=ai/mistral:7B-Q4_K_M
```
