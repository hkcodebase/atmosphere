# atmosphere
ai enabled weather app


## Prerequisites
- Docker Desktop with AI features enabled
- uv package manager
- Gemma4 model available in Docker (run `docker model install ai/gemma4` if needed)

## start the application:
```bash
 cd src && uv run client.py weather.py
```

## References & Technical Stack

*   **Model:** [Google Gemma 4](https://blog.google/technology/ai/gemma-4-open-model/) — Small but powerful open-source model optimized for tool-use and reasoning.
*   **Protocol:** [Model Context Protocol (MCP)](https://modelcontextprotocol.io) — An open standard that enables LLMs to safely access local data and tools.
*   **Containerization:** [Docker](https://www.docker.com/) — Ensures the MCP server environment is isolated and reproducible.
*   **Weather Data:** [Weather API](https://api.weather.gov) (or your chosen provider).


## Known Limitations
*   **Geographic Scope:** Currently optimized for US/Global cities only.
*   **Rate Limits:** Subject to the API limits of the weather provider.
*   **Hardware Requirements:** Requires at least 8GB of RAM to run Gemma 4 smoothly within Docker.

