import logging
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI

# Initialize FastMCP server
mcp = FastMCP("weather")

# Initialize FastAPI app
app = FastAPI()

# Store the MCP instance for access in endpoints
mcp_instance = None

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


async def make_geocode_request(url: str) -> list[dict] | None:
    """Make a request to the geocoding API."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
            Event: {props.get("event", "Unknown")}
            Area: {props.get("areaDesc", "Unknown")}
            Severity: {props.get("severity", "Unknown")}
            Description: {props.get("description", "No description available")}
            Instructions: {props.get("instruction", "No specific instructions provided")}
            """


@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
                    {period["name"]}:
                    Temperature: {period["temperature"]}°{period["temperatureUnit"]}
                    Wind: {period["windSpeed"]} {period["windDirection"]}
                    Forecast: {period["detailedForecast"]}
                    """
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)


@mcp.tool()
async def get_location(location: str) -> str:
    """Get latitude and longitude for a location.

    Args:
        location: Location name (e.g. "New York City")
    """
    url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1"
    data = await make_geocode_request(url)

    if data and len(data) > 0:
        lat = data[0]['lat']
        lon = data[0]['lon']
        return f"Latitude: {lat}, Longitude: {lon}"
    else:
        return "Location not found"


def main():
    logging.info("starting weather app")
    # Run the MCP server
    mcp.run()


# Add HTTP endpoints for testing
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "weather"}


@app.post("/api/get_location")
async def http_get_location(location: str):
    """HTTP endpoint for get_location."""
    return {"result": await get_location(location)}


@app.post("/api/get_forecast")
async def http_get_forecast(latitude: float, longitude: float):
    """HTTP endpoint for get_forecast."""
    return {"result": await get_forecast(latitude, longitude)}


@app.post("/api/get_alerts")
async def http_get_alerts(state: str):
    """HTTP endpoint for get_alerts."""
    return {"result": await get_alerts(state)}


@app.get("/api/tools")
async def list_tools():
    """List all available tools."""
    return {
        "tools": [
            {
                "name": "get_location",
                "description": "Get latitude and longitude for a location",
                "params": {"location": "string"}
            },
            {
                "name": "get_forecast",
                "description": "Get weather forecast for a location",
                "params": {"latitude": "float", "longitude": "float"}
            },
            {
                "name": "get_alerts",
                "description": "Get weather alerts for a US state",
                "params": {"state": "string (2-letter state code)"}
            }
        ]
    }


if __name__ == "__main__":
    main()