import os
import httpx
from langchain_core.tools import tool


API_BASE = os.getenv("WEATHER_API_BASE", "http://127.0.0.1:8000")


def _post(path: str, payload: dict):
    resp = httpx.post(f"{API_BASE}{path}", json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()["result"]


@tool
def get_location(location: str) -> str:
    """Get latitude/longitude for a city."""
    return _post("/api/get_location", {"location": location})


@tool
def get_forecast_by_location(location: str) -> str:
    """Get weather forecast for a city."""
    loc = _post("/api/get_location", {"location": location})

    import re
    lat = re.search(r"Latitude:\s*([\d.-]+)", loc).group(1)
    lon = re.search(r"Longitude:\s*([\d.-]+)", loc).group(1)

    return _post(
        "/api/get_forecast",
        {"latitude": float(lat), "longitude": float(lon)},
    )


@tool
def get_alerts(state: str) -> str:
    """Get weather alerts for a US state."""
    return _post("/api/get_alerts", {"state": state})