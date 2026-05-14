# atmosphere
ai enabled weather app


## Prerequisites
- Docker Desktop with AI features enabled
- [uv package manager](https://docs.astral.sh/uv/)
- Gemma4 model available in Docker (run `docker model install ai/gemma4` if needed)

## Project Structure
```
src/
├── mcp_client/        # MCP client for connecting to the server
│   └── client.py
├── mcp_server/        # Weather MCP server
│   └── weather_mcp_server.py
└── test/              # Unit tests
    └── test_weather_mcp_server.py
```

## start the application:
```bash
cd src && uv run mcp_client.client mcp_server.weather_mcp_server
```

## Running Tests
To run the unit tests locally:
```bash
cd src && uv run pytest test/ -v
```

To run tests with coverage:
```bash
cd src && uv run pytest test/ --cov=mcp_server --cov-report=term-missing
```

## HTTP Endpoints for Testing
The server also provides HTTP endpoints for direct testing:
- `GET /health` - Health check
- `POST /api/get_location` - Get coordinates for a location
- `POST /api/get_forecast` - Get weather forecast
- `POST /api/get_alerts` - Get weather alerts
- `GET /api/tools` - List available tools

To run the HTTP server for testing:
```bash
cd src && uv run uvicorn mcp_server.weather_mcp_server:app --host 127.0.0.1 --port 8000
```
Note: This runs the FastAPI server instead of the MCP server. Use for API testing only.

## References & Technical Stack

*   **Model:** [Google Gemma 4](https://blog.google/technology/ai/gemma-4-open-model/) — Small but powerful open-source model optimized for tool-use and reasoning.
*   **Protocol:** [Model Context Protocol (MCP)](https://modelcontextprotocol.io) — An open standard that enables LLMs to safely access local data and tools.
*   **Containerization:** [Docker](https://www.docker.com/) — Ensures the MCP server environment is isolated and reproducible.
*   **Weather Data:** [Weather API](https://api.weather.gov) (or your chosen provider).


## Known Limitations
*   **Geographic Scope:** Currently optimized for US/Global cities only.
*   **Rate Limits:** Subject to the API limits of the weather provider.
*   **Hardware Requirements:** Requires at least 8GB of RAM to run Gemma 4 smoothly within Docker.
