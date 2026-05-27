import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from mcp_server.weather_mcp_server import (
    get_location,
    get_forecast,
    get_alerts,
    format_alert,
    make_nws_request,
    make_geocode_request,
    app,
)


# Initialize test client
client = TestClient(app)


# ============================================================================
# TEST: get_location() Function
# ============================================================================


class TestGetLocation:
    @pytest.mark.asyncio
    async def test_get_location_success(self):
        """Test successful location lookup."""
        mock_response_data = [
            {
                "lat": "40.7128",
                "lon": "-74.0060",
                "display_name": "New York City, New York, United States",
            }
        ]
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = await get_location("New York City")
            assert "Location: New York City, New York, United States" in result
            assert "Latitude: 40.7128" in result
            assert "Longitude: -74.0060" in result

    @pytest.mark.asyncio
    async def test_get_location_not_found(self):
        """Test location not found."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = []
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = await get_location("Nonexistent Place XYZ 123")
            assert "Location 'Nonexistent Place XYZ 123' not found" == result

    @pytest.mark.asyncio
    async def test_get_location_empty_string(self):
        """Test location with empty string."""
        result = await get_location("")
        assert result == "Error: location parameter is required"

    @pytest.mark.asyncio
    async def test_get_location_whitespace_only(self):
        """Test location with whitespace only."""
        result = await get_location("   ")
        assert result == "Error: location parameter is required"

    @pytest.mark.asyncio
    async def test_get_location_http_error(self):
        """Test location lookup with HTTP error."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("404 Not Found")
            mock_get.return_value = mock_response

            result = await get_location("San Francisco")
            assert "Location 'San Francisco' not found" == result

    @pytest.mark.asyncio
    async def test_get_location_with_display_name(self):
        """Test location lookup returns display_name properly."""
        mock_response_data = [
            {
                "lat": "51.5074",
                "lon": "-0.1278",
                "display_name": "London, United Kingdom",
            }
        ]
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = await get_location("London")
            assert "Location: London, United Kingdom" in result


# ============================================================================
# TEST: get_forecast() Function
# ============================================================================


class TestGetForecast:
    @pytest.mark.asyncio
    async def test_get_forecast_success(self):
        """Test successful forecast retrieval."""
        points_data = {
            "properties": {
                "forecast": "https://api.weather.gov/gridpoints/OKX/33,35/forecast"
            }
        }
        forecast_data = {
            "properties": {
                "periods": [
                    {
                        "name": "Tonight",
                        "temperature": 65,
                        "temperatureUnit": "F",
                        "windSpeed": "5 mph",
                        "windDirection": "SW",
                        "detailedForecast": "Clear skies",
                    },
                    {
                        "name": "Tomorrow",
                        "temperature": 75,
                        "temperatureUnit": "F",
                        "windSpeed": "10 mph",
                        "windDirection": "NW",
                        "detailedForecast": "Sunny",
                    },
                ]
            }
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_points_response = Mock()
            mock_points_response.json.return_value = points_data
            mock_points_response.raise_for_status.return_value = None

            mock_forecast_response = Mock()
            mock_forecast_response.json.return_value = forecast_data
            mock_forecast_response.raise_for_status.return_value = None

            mock_get.side_effect = [mock_points_response, mock_forecast_response]

            result = await get_forecast(40.7128, -74.0060)
            assert "Tonight:" in result
            assert "Tomorrow:" in result
            assert "65°F" in result
            assert "Clear skies" in result

    @pytest.mark.asyncio
    async def test_get_forecast_failure(self):
        """Test forecast retrieval with network error."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = Exception("Network error")

            result = await get_forecast(40.7128, -74.0060)
            assert "Unable to fetch forecast data" in result

    @pytest.mark.asyncio
    async def test_get_forecast_outside_coverage(self):
        """Test forecast for location outside NWS coverage area."""
        points_data = {"properties": {}}  # Missing "forecast" key

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = points_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = await get_forecast(40.7128, -74.0060)
            assert "Location is outside NWS coverage area or invalid" in result

    @pytest.mark.asyncio
    async def test_get_forecast_invalid_points_response(self):
        """Test forecast with invalid points response structure."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = None
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = await get_forecast(40.7128, -74.0060)
            assert "Unable to fetch forecast data" in result

    @pytest.mark.asyncio
    async def test_get_forecast_failed_forecast_fetch(self):
        """Test forecast when forecast endpoint fails."""
        points_data = {
            "properties": {
                "forecast": "https://api.weather.gov/gridpoints/OKX/33,35/forecast"
            }
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_points_response = Mock()
            mock_points_response.json.return_value = points_data
            mock_points_response.raise_for_status.return_value = None

            # Second call (forecast) returns None
            mock_get.side_effect = [mock_points_response, None]

            result = await get_forecast(40.7128, -74.0060)
            assert "Unable to fetch detailed forecast" in result

    @pytest.mark.asyncio
    async def test_get_forecast_only_5_periods(self):
        """Test that forecast returns only first 5 periods."""
        points_data = {
            "properties": {
                "forecast": "https://api.weather.gov/gridpoints/OKX/33,35/forecast"
            }
        }
        # Create 10 periods to verify only first 5 are returned
        periods = [
            {
                "name": f"Period {i}",
                "temperature": 60 + i,
                "temperatureUnit": "F",
                "windSpeed": f"{5 * i} mph",
                "windDirection": "N",
                "detailedForecast": f"Forecast {i}",
            }
            for i in range(10)
        ]
        forecast_data = {"properties": {"periods": periods}}

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_points_response = Mock()
            mock_points_response.json.return_value = points_data
            mock_points_response.raise_for_status.return_value = None

            mock_forecast_response = Mock()
            mock_forecast_response.json.return_value = forecast_data
            mock_forecast_response.raise_for_status.return_value = None

            mock_get.side_effect = [mock_points_response, mock_forecast_response]

            result = await get_forecast(40.7128, -74.0060)
            # Should have first 5 periods
            assert "Period 0:" in result
            assert "Period 4:" in result
            # Should NOT have 6th period
            assert "Period 5:" not in result


# ============================================================================
# TEST: get_alerts() Function
# ============================================================================


class TestGetAlerts:
    @pytest.mark.asyncio
    async def test_get_alerts_success(self):
        """Test successful alerts retrieval."""
        alerts_data = {
            "features": [
                {
                    "properties": {
                        "event": "Flood Warning",
                        "areaDesc": "New York City",
                        "severity": "Moderate",
                        "description": "Flooding expected",
                        "instruction": "Evacuate low areas",
                    }
                }
            ]
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = alerts_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = await get_alerts("NY")
            assert "Flood Warning" in result
            assert "New York City" in result
            assert "Moderate" in result

    @pytest.mark.asyncio
    async def test_get_alerts_multiple(self):
        """Test alerts retrieval with multiple active alerts."""
        alerts_data = {
            "features": [
                {
                    "properties": {
                        "event": "Flood Warning",
                        "areaDesc": "New York City",
                        "severity": "Moderate",
                        "description": "Flooding expected",
                        "instruction": "Evacuate low areas",
                    }
                },
                {
                    "properties": {
                        "event": "Winter Storm Warning",
                        "areaDesc": "Upstate New York",
                        "severity": "Severe",
                        "description": "Heavy snow expected",
                        "instruction": "Stay indoors",
                    }
                },
            ]
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = alerts_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = await get_alerts("NY")
            assert "Flood Warning" in result
            assert "Winter Storm Warning" in result
            assert result.count("---") == 1  # Separator between alerts

    @pytest.mark.asyncio
    async def test_get_alerts_no_alerts(self):
        """Test alerts retrieval when no active alerts."""
        alerts_data = {"features": []}

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = alerts_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = await get_alerts("CA")
            assert "No active weather alerts for CA" == result

    @pytest.mark.asyncio
    async def test_get_alerts_failure(self):
        """Test alerts retrieval with network error."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = Exception("Network error")

            result = await get_alerts("TX")
            assert "Unable to fetch alerts for state 'TX'" == result

    @pytest.mark.asyncio
    async def test_get_alerts_empty_state(self):
        """Test alerts with empty state code."""
        result = await get_alerts("")
        assert result == "Error: state parameter is required"

    @pytest.mark.asyncio
    async def test_get_alerts_whitespace_state(self):
        """Test alerts with whitespace-only state code."""
        result = await get_alerts("   ")
        assert result == "Error: state parameter is required"

    @pytest.mark.asyncio
    async def test_get_alerts_lowercase_state(self):
        """Test alerts converts state to uppercase."""
        alerts_data = {"features": []}

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = alerts_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = await get_alerts("ca")
            assert "No active weather alerts for CA" == result

    @pytest.mark.asyncio
    async def test_get_alerts_no_features_key(self):
        """Test alerts when response has no features key."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = await get_alerts("NY")
            assert "Unable to fetch alerts for state 'NY'" == result


# ============================================================================
# TEST: format_alert() Function
# ============================================================================


class TestFormatAlert:
    def test_format_alert_complete(self):
        """Test format_alert with complete alert data."""
        feature = {
            "properties": {
                "event": "Tornado Warning",
                "areaDesc": "New York County",
                "severity": "Extreme",
                "description": "A tornado has been sighted",
                "instruction": "Take shelter immediately",
            }
        }
        result = format_alert(feature)
        assert "Event: Tornado Warning" in result
        assert "Area: New York County" in result
        assert "Severity: Extreme" in result
        assert "Description: A tornado has been sighted" in result
        assert "Instructions: Take shelter immediately" in result

    def test_format_alert_partial(self):
        """Test format_alert with missing properties."""
        feature = {
            "properties": {
                "event": "Wind Advisory",
            }
        }
        result = format_alert(feature)
        assert "Event: Wind Advisory" in result
        assert "Area: Unknown" in result
        assert "Severity: Unknown" in result
        assert "No description available" in result

    def test_format_alert_empty_properties(self):
        """Test format_alert with empty properties."""
        feature = {"properties": {}}
        result = format_alert(feature)
        assert "Event: Unknown" in result
        assert "Area: Unknown" in result

    def test_format_alert_no_properties(self):
        """Test format_alert with no properties key."""
        feature = {}
        result = format_alert(feature)
        assert "Event: Unknown" in result


# ============================================================================
# TEST: HTTP Endpoints
# ============================================================================


class TestHTTPEndpoints:
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "weather-mcp-server"

    def test_server_info(self):
        """Test server info endpoint."""
        response = client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Weather MCP Server"
        assert "tools" in data
        assert "get_location" in data["tools"]
        assert "get_forecast" in data["tools"]
        assert "get_alerts" in data["tools"]

    def test_list_tools(self):
        """Test tools list endpoint."""
        response = client.get("/api/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) == 3
        tool_names = [tool["name"] for tool in data["tools"]]
        assert "get_location" in tool_names
        assert "get_forecast" in tool_names
        assert "get_alerts" in tool_names

    def test_http_get_location_success(self):
        """Test HTTP POST endpoint for get_location."""
        mock_response_data = [
            {"lat": "40.7128", "lon": "-74.0060", "display_name": "New York City"}
        ]
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            response = client.post("/api/get_location", json={"location": "New York"})
            assert response.status_code == 200
            data = response.json()
            assert "result" in data
            assert "Latitude: 40.7128" in data["result"]

    def test_http_get_location_invalid_request(self):
        """Test HTTP endpoint with invalid request (missing location)."""
        response = client.post("/api/get_location", json={})
        assert response.status_code == 422  # Validation error

    def test_http_get_location_empty_string(self):
        """Test HTTP endpoint with empty location string."""
        response = client.post("/api/get_location", json={"location": ""})
        assert response.status_code == 422  # Validation error (min_length=1)

    def test_http_get_forecast_success(self):
        """Test HTTP POST endpoint for get_forecast."""
        points_data = {
            "properties": {
                "forecast": "https://api.weather.gov/gridpoints/OKX/33,35/forecast"
            }
        }
        forecast_data = {
            "properties": {
                "periods": [
                    {
                        "name": "Tonight",
                        "temperature": 65,
                        "temperatureUnit": "F",
                        "windSpeed": "5 mph",
                        "windDirection": "SW",
                        "detailedForecast": "Clear",
                    }
                ]
            }
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_points_response = Mock()
            mock_points_response.json.return_value = points_data
            mock_points_response.raise_for_status.return_value = None

            mock_forecast_response = Mock()
            mock_forecast_response.json.return_value = forecast_data
            mock_forecast_response.raise_for_status.return_value = None

            mock_get.side_effect = [mock_points_response, mock_forecast_response]

            response = client.post(
                "/api/get_forecast", json={"latitude": 40.7128, "longitude": -74.0060}
            )
            assert response.status_code == 200
            data = response.json()
            assert "result" in data

    def test_http_get_forecast_invalid_latitude(self):
        """Test HTTP endpoint with invalid latitude (out of bounds)."""
        response = client.post(
            "/api/get_forecast", json={"latitude": 91.0, "longitude": -74.0060}
        )
        assert response.status_code == 422  # Validation error

    def test_http_get_forecast_invalid_longitude(self):
        """Test HTTP endpoint with invalid longitude (out of bounds)."""
        response = client.post(
            "/api/get_forecast", json={"latitude": 40.7128, "longitude": 181.0}
        )
        assert response.status_code == 422  # Validation error

    def test_http_get_forecast_missing_field(self):
        """Test HTTP endpoint with missing latitude."""
        response = client.post(
            "/api/get_forecast", json={"latitude": 40.7128}
        )
        assert response.status_code == 422  # Validation error

    def test_http_get_alerts_success(self):
        """Test HTTP POST endpoint for get_alerts."""
        alerts_data = {
            "features": [
                {
                    "properties": {
                        "event": "Flood Warning",
                        "areaDesc": "New York City",
                        "severity": "Moderate",
                        "description": "Flooding",
                        "instruction": "Evacuate",
                    }
                }
            ]
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = alerts_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            response = client.post("/api/get_alerts", json={"state": "NY"})
            assert response.status_code == 200
            data = response.json()
            assert "result" in data
            assert "Flood Warning" in data["result"]

    def test_http_get_alerts_invalid_state_code(self):
        """Test HTTP endpoint with invalid state code length."""
        response = client.post("/api/get_alerts", json={"state": "NYC"})
        assert response.status_code == 422  # Validation error (max_length=2)

    def test_http_get_alerts_empty_state(self):
        """Test HTTP endpoint with empty state."""
        response = client.post("/api/get_alerts", json={"state": ""})
        assert response.status_code == 422  # Validation error (min_length=2)

    def test_http_get_alerts_missing_field(self):
        """Test HTTP endpoint with missing state field."""
        response = client.post("/api/get_alerts", json={})
        assert response.status_code == 422  # Validation error
