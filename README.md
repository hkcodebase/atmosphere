# Atmosphere ☁️

**Version 1.0** | **Last Updated: 2026-05-17** | **Status: Production Ready ✅**

An AI-enabled weather assistant using **Model Context Protocol (MCP)**, **LangGraph**, and **Google Gemma 4**. Built for local execution with zero cloud dependencies.

## Key Features

✅ **MCP-Based Architecture** - Standards-compliant Model Context Protocol  
✅ **Local LLM** - Google Gemma 4 running locally via Docker  
✅ **Intelligent Agents** - LangGraph-powered agentic workflows  
✅ **Tool Calling** - Automatic weather tool execution  
✅ **REST API** - FastAPI endpoints for direct integration  
✅ **Production Tests** - 81 comprehensive tests with 95% coverage  
✅ **Zero Cloud APIs** - Completely self-contained execution

---

## System Architecture

```
┌─────────────────────────────────┐
│    User Chat (Interactive)      │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│   LangGraph Agent Workflow      │
│  • State Management             │
│  • Tool Calling                 │
│  • Message Routing              │
└──────────────┬──────────────────┘
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
  ┌────────┐      ┌──────────────┐
  │ Gemma4 │      │ Tools Node   │
  │  LLM   │      │              │
  └────────┘      │ • Location   │
                  │ • Forecast   │
                  │ • Alerts     │
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │ Weather APIs │
                  │              │
                  │ • Nominatim  │
                  │ • NWS API    │
                  └──────────────┘
```


```text
 +-------------------+       MCP / HTTP       +----------------------+
 |   MCP Client      |  <------------------>  |  Weather MCP Server  |
 |  (Gemma 4 + CLI)  |       Tool Calls       |  (FastAPI + Tools)   |
 +-------------------+                        +----------------------+
          |                                              |
          |                                              | Weather APIs
          v                                              v
 +-------------------+                        +----------------------+
 | Local Gemma 4 LLM |                        | National Weather API |
 | (Docker Model)    |                        | api.weather.gov      |
 +-------------------+                        +----------------------+
```

---

# Features

* MCP-based AI weather assistant
* Local LLM execution using Gemma 4 (no cloud API key required)
* Interactive CLI chat experience
* Tool calling support:

    * `get_location`
    * `get_forecast`
    * `get_alerts`
* FastAPI endpoints for direct testing
* Configurable via environment variables
* Unit testing with pytest
* Docker-enabled local AI execution

---

# Project Structure

```text
atmosphere/
├─ src/
   ├── mcp_client/              # LangGraph Agent
   │   ├── client.py            # Chat interface
   │   ├── graph.py             # LangGraph workflow
   │   ├── graph_nodes.py       # Agent/tool nodes
   │   ├── tools_lc.py          # Tool definitions
   │   ├── llm.py               # LLM config
   │   └── state.py             # State schema
   │
   ├── mcp_server/              # Weather Server
   │   └── weather_mcp_server.py # FastAPI + MCP
   │
   └── test/                    # 81 Comprehensive Tests
       ├── test_weather_mcp_server.py (38 tests)
       └── test_mcp_client.py (43 tests)
```

---

---

# Prerequisites

- **Docker Desktop** - For Gemma 4 local execution
- **Python 3.14+** - For runtime
- **uv** - Package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

---

# Install Dependencies

## 1. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify installation:

```bash
uv --version
```

---

## 2. Install Docker Desktop

Download and install Docker Desktop:

[Docker Desktop](https://www.docker.com/products/docker-desktop/?utm_source=chatgpt.com)

Verify installation:

```bash
docker --version
```

---

## 3. Install Gemma 4 Model

Pull the local Gemma 4 model into Docker:

```bash
docker model install ai/gemma4
```

This is a one-time setup step.

---

# Running the Application

## Step 1 — Start the MCP Weather Server

Open Terminal 1:

```bash
cd src

uv run uvicorn mcp_server.weather_mcp_server:app \
  --host 127.0.0.1 \
  --port 8000
```

The server will expose:

* MCP tools
* HTTP APIs
* Health endpoints

---

## Step 2 — Start the MCP Client

Open Terminal 2:

```bash
cd src

uv run mcp_client/client.py
```

The client will:

1. Connect to the MCP server
2. Use local Gemma 4 for reasoning
3. Detect tool calls from the LLM
4. Execute weather tools automatically
5. Return results in an interactive chat session

---

# Example Queries

```text
What is the weather forecast for New York City?

What are the weather alerts for California?

Show forecast for Chicago for the next 24 hours.
```

---

# Environment Configuration

The application can be customized using environment variables.

---

## Default Configuration

| Variable                  | Default Value                                  |
| ------------------------- | ---------------------------------------------- |
| WEATHER_API_BASE          | [http://127.0.0.1:8000](http://127.0.0.1:8000) |
| WEATHER_TOOLS_PATH        | /api/tools                                     |
| WEATHER_GET_LOCATION_PATH | /api/get_location                              |
| WEATHER_GET_FORECAST_PATH | /api/get_forecast                              |
| WEATHER_GET_ALERTS_PATH   | /api/get_alerts                                |

---

## Full Environment Variables

| Variable                  | Description                |
| ------------------------- | -------------------------- |
| WEATHER_API_BASE          | Base server URL            |
| WEATHER_TOOLS_URL         | Full tools endpoint URL    |
| WEATHER_TOOLS_PATH        | Tools endpoint path        |
| WEATHER_GET_LOCATION_URL  | Full get_location URL      |
| WEATHER_GET_LOCATION_PATH | get_location endpoint path |
| WEATHER_GET_FORECAST_URL  | Full get_forecast URL      |
| WEATHER_GET_FORECAST_PATH | get_forecast endpoint path |
| WEATHER_GET_ALERTS_URL    | Full get_alerts URL        |
| WEATHER_GET_ALERTS_PATH   | get_alerts endpoint path   |

---

# Configuration Examples

## Use a Different Server

```bash
cd src

uv run mcp_client/client.py http://192.0.2.10:8080
```

---

## Override Forecast Endpoint

```bash
export WEATHER_GET_FORECAST_PATH="/custom/forecast"

cd src
uv run mcp_client/client.py
```

---

## Override Base URL

```bash
export WEATHER_API_BASE="https://api-host:8443"

cd src
uv run mcp_client/client.py
```

---

---

# HTTP API Endpoints

## Health & Info
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/info` | Server info |
| GET | `/api/tools` | List available tools |

## Weather Tools
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/get_location` | Resolve location to coordinates |
| POST | `/api/get_forecast` | Get weather forecast |
| POST | `/api/get_alerts` | Get weather alerts |

The server also exposes REST endpoints for direct testing.

| Method | Endpoint            | Description           |
| ------ | ------------------- | --------------------- |
| GET    | `/health`           | Health check          |
| GET    | `/api/tools`        | List MCP tools        |
| POST   | `/api/get_location` | Resolve city/location |
| POST   | `/api/get_forecast` | Weather forecast      |
| POST   | `/api/get_alerts`   | Weather alerts        |

---

## Example API Test

```bash
curl -X POST http://127.0.0.1:8000/api/get_location \
  -H "Content-Type: application/json" \
  -d '{"location": "New York City"}'
```

---

# Running Tests

## Run All Tests

```bash
cd src

uv run pytest test/ -v
```

---

## Run Tests with Coverage

```bash
cd src

uv run pytest test/ \
  --cov=mcp_server \
  --cov-report=term-missing
```

---

## Run Specific Test

```bash
cd src

uv run pytest \
  test/test_weather_mcp_server.py::TestWeatherMCPServer::test_get_location_success \
  -v
```

**Test Results**: ✅ 81/81 passing | ~95% coverage

---

# Technical Stack

| Component        | Technology                   |
| ---------------- | ---------------------------- |
| LLM              | Google Gemma 4               |
| Protocol         | Model Context Protocol (MCP) |
| Backend          | FastAPI                      |
| Runtime          | Python                       |
| Containerization | Docker                       |
| Package Manager  | uv                           |
| Testing          | pytest                       |
| Weather Provider | api.weather.gov              |

---

# References

* [Google Gemma 4](https://blog.google/technology/ai/gemma-4-open-model/?utm_source=chatgpt.com)
* [Model Context Protocol (MCP)](https://modelcontextprotocol.io?utm_source=chatgpt.com)
* [Docker](https://www.docker.com/?utm_source=chatgpt.com)
* [National Weather Service API](https://api.weather.gov?utm_source=chatgpt.com)
* [uv Package Manager](https://docs.astral.sh/uv/?utm_source=chatgpt.com)

---

# Known Limitations

* Optimized primarily for US/global city forecasts
* Dependent on weather provider rate limits
* Requires approximately 8GB RAM for smooth local Gemma 4 execution
* Local inference performance depends on Docker resource allocation

---

# Future Enhancements

* Multi-agent MCP orchestration
* Streaming responses
* Web UI dashboard
* Redis caching layer
* Conversation memory
* Observability and tracing
* Support for additional weather providers
* LangGraph-based agent workflows
