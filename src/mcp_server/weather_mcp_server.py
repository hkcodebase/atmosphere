"""
Weather MCP Server with FastAPI
Supports both MCP protocol and HTTP endpoints for testing/development
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Constants
NWS_API_BASE = "https://api.weather.gov"
NOMINATIM_API_BASE = "https://nominatim.openstreetmap.org"
USER_AGENT = "weather-mcp-server/1.0 (MCP Server)"
REQUEST_TIMEOUT = 30.0

# Initialize FastMCP server
mcp = FastMCP("weather")


# ============================================================================
# API Request Handlers
# ============================================================================


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS (National Weather Service) API."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            logger.debug(f"NWS API request successful: {url}")
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"NWS API error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in NWS request: {e}")
            return None


async def make_geocode_request(url: str) -> list[dict] | None:
    """Make a request to the Nominatim geocoding API."""
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            logger.debug(f"Geocoding API request successful: {url}")
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Geocoding API error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in geocoding request: {e}")
            return None


def format_alert(feature: dict) -> str:
    """Format a weather alert feature into readable text."""
    props = feature.get("properties", {})
    return f"""Event: {props.get("event", "Unknown")}
Area: {props.get("areaDesc", "Unknown")}
Severity: {props.get("severity", "Unknown")}
Description: {props.get("description", "No description available")}
Instructions: {props.get("instruction", "No specific instructions provided")}"""


# ============================================================================
# MCP Tools
# ============================================================================


@mcp.tool()
async def get_location(location: str) -> str:
    """Get latitude and longitude for a location using Nominatim geocoding.

    Args:
        location: Location name (e.g. "New York City", "San Francisco, CA")

    Returns:
        A string with latitude and longitude coordinates, or error message.
    """
    if not location or not location.strip():
        return "Error: location parameter is required"

    location = location.strip()
    logger.info(f"Getting location for: {location}")

    url = f"{NOMINATIM_API_BASE}/search?q={location}&format=json&limit=1"
    data = await make_geocode_request(url)

    if data and len(data) > 0:
        lat = data[0]["lat"]
        lon = data[0]["lon"]
        display_name = data[0].get("display_name", location)
        logger.info(f"Found coordinates for {location}: {lat}, {lon}")
        return f"Location: {display_name}\nLatitude: {lat}\nLongitude: {lon}"
    else:
        logger.warning(f"Location not found: {location}")
        return f"Location '{location}' not found"


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location using NWS API.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location

    Returns:
        A formatted string with the next 5 forecast periods.
    """
    logger.info(f"Getting forecast for lat={latitude}, lon={longitude}")

    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        logger.error(f"Failed to fetch points data for {latitude},{longitude}")
        return "Error: Unable to fetch forecast data for this location"

    # Extract the forecast URL
    try:
        forecast_url = points_data["properties"]["forecast"]
    except (KeyError, TypeError) as e:
        logger.error(f"Invalid points response: {e}")
        return "Error: Location is outside NWS coverage area or invalid"

    # Get the detailed forecast
    forecast_data = await make_nws_request(forecast_url)
    if not forecast_data:
        logger.error(f"Failed to fetch forecast from {forecast_url}")
        return "Error: Unable to fetch detailed forecast"

    # Format the forecast periods
    try:
        periods = forecast_data["properties"]["periods"]
        forecasts = []
        for period in periods[:5]:  # Only show next 5 periods
            forecast = f"""{period["name"]}:
Temperature: {period["temperature"]}°{period["temperatureUnit"]}
Wind: {period["windSpeed"]} {period["windDirection"]}
Forecast: {period["detailedForecast"]}"""
            forecasts.append(forecast)
        result = "\n---\n".join(forecasts)
        logger.info("Forecast retrieved successfully")
        return result
    except (KeyError, IndexError) as e:
        logger.error(f"Error formatting forecast: {e}")
        return "Error: Unable to parse forecast data"


@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get active weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. "CA", "NY", "TX")

    Returns:
        A formatted string with active weather alerts, or a message if none exist.
    """
    if not state or not state.strip():
        return "Error: state parameter is required"

    state = state.upper().strip()
    logger.info(f"Getting alerts for state: {state}")

    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        logger.warning(f"Unable to fetch alerts for {state}")
        return f"Unable to fetch alerts for state '{state}'"

    if not data["features"]:
        logger.info(f"No active alerts for {state}")
        return f"No active weather alerts for {state}"

    try:
        alerts = [format_alert(feature) for feature in data["features"]]
        result = "\n---\n".join(alerts)
        logger.info(f"Found {len(alerts)} alerts for {state}")
        return result
    except Exception as e:
        logger.error(f"Error formatting alerts: {e}")
        return "Error: Unable to parse alert data"


# ============================================================================
# Pydantic Request Models
# ============================================================================


class LocationRequest(BaseModel):
    """Request model for location endpoint."""
    location: str = Field(..., min_length=1, description="Location name to geocode")


class ForecastRequest(BaseModel):
    """Request model for forecast endpoint."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")


class AlertsRequest(BaseModel):
    """Request model for alerts endpoint."""
    state: str = Field(..., min_length=2, max_length=2, description="Two-letter US state code")


# ============================================================================
# FastAPI App Setup
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for app startup/shutdown."""
    logger.info("Starting Weather MCP Server")
    yield
    logger.info("Shutting down Weather MCP Server")


app = FastAPI(
    title="Weather MCP Server",
    description="MCP Server for weather information using NWS and Nominatim APIs",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================================
# Health & Info Endpoints
# ============================================================================


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    logger.debug("Health check requested")
    return {"status": "healthy", "service": "weather-mcp-server"}


@app.get("/info", tags=["info"])
async def server_info():
    """Server information endpoint."""
    return {
        "name": "Weather MCP Server",
        "version": "1.0.0",
        "description": "MCP Server for weather information",
        "tools": ["get_location", "get_forecast", "get_alerts"],
    }


# ============================================================================
# HTTP Tool Endpoints (for testing/development)
# ============================================================================


@app.post("/api/get_location", tags=["tools"])
async def http_get_location(req: LocationRequest):
    """Get coordinates for a location.

    Request body: {"location": "New York City"}
    """
    try:
        result = await get_location(req.location)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error in get_location: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/get_forecast", tags=["tools"])
async def http_get_forecast(req: ForecastRequest):
    """Get weather forecast for coordinates.

    Request body: {"latitude": 40.7128, "longitude": -74.0060}
    """
    try:
        result = await get_forecast(req.latitude, req.longitude)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error in get_forecast: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/get_alerts", tags=["tools"])
async def http_get_alerts(req: AlertsRequest):
    """Get weather alerts for a US state.

    Request body: {"state": "NY"}
    """
    try:
        result = await get_alerts(req.state)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error in get_alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/tools", tags=["info"])
async def list_tools():
    """List all available tools with descriptions."""
    return {
        "tools": [
            {
                "name": "get_location",
                "description": "Get latitude and longitude for a location",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "Location name"}
                    },
                    "required": ["location"],
                },
            },
            {
                "name": "get_forecast",
                "description": "Get weather forecast for a location",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "latitude": {"type": "number", "description": "Latitude"},
                        "longitude": {"type": "number", "description": "Longitude"},
                    },
                    "required": ["latitude", "longitude"],
                },
            },
            {
                "name": "get_alerts",
                "description": "Get weather alerts for a US state",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "state": {
                            "type": "string",
                            "description": "Two-letter US state code",
                        }
                    },
                    "required": ["state"],
                },
            },
        ]
    }


# ============================================================================
# MCP Server Mount
# ============================================================================


app.mount("/mcp", mcp.streamable_http_app())


# ============================================================================
# Main Entry Point
# ============================================================================


if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI app with Uvicorn
    # The MCP protocol is available at /mcp
    # HTTP endpoints are at /api/*
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
