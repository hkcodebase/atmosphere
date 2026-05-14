import pytest
from unittest.mock import patch, Mock
from mcp_server.weather_mcp_server import get_location, get_forecast, get_alerts


class TestWeatherMCPServer:
    @pytest.mark.asyncio
    async def test_get_location_success(self):
        mock_response_data = [{"lat": "40.7128", "lon": "-74.0060"}]
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = await get_location("New York City")
            assert "Latitude: 40.7128, Longitude: -74.0060" in result

    @pytest.mark.asyncio
    async def test_get_location_not_found(self):
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = []
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = await get_location("Nonexistent Place")
            assert result == "Location not found"

    @pytest.mark.asyncio
    async def test_get_forecast_success(self):
        # Mock points response
        points_data = {
            "properties": {
                "forecast": "https://api.weather.gov/gridpoints/OKX/33,35/forecast"
            }
        }
        # Mock forecast response
        forecast_data = {
            "properties": {
                "periods": [
                    {
                        "name": "Tonight",
                        "temperature": 65,
                        "temperatureUnit": "F",
                        "windSpeed": "5 mph",
                        "windDirection": "SW",
                        "detailedForecast": "Clear skies"
                    },
                    {
                        "name": "Tomorrow",
                        "temperature": 75,
                        "temperatureUnit": "F",
                        "windSpeed": "10 mph",
                        "windDirection": "NW",
                        "detailedForecast": "Sunny"
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

            result = await get_forecast(40.7128, -74.0060)
            assert "Tonight:" in result
            assert "Tomorrow:" in result
            assert "65°F" in result

    @pytest.mark.asyncio
    async def test_get_forecast_failure(self):
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = Exception("Network error")

            result = await get_forecast(40.7128, -74.0060)
            assert "Unable to fetch forecast data" in result

    @pytest.mark.asyncio
    async def test_get_alerts_success(self):
        alerts_data = {
            "features": [
                {
                    "properties": {
                        "event": "Flood Warning",
                        "areaDesc": "New York City",
                        "severity": "Moderate",
                        "description": "Flooding expected",
                        "instruction": "Evacuate low areas"
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

    @pytest.mark.asyncio
    async def test_get_alerts_no_alerts(self):
        alerts_data = {"features": []}

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = alerts_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = await get_alerts("CA")
            assert "No active alerts" in result

    @pytest.mark.asyncio
    async def test_get_alerts_failure(self):
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = Exception("Network error")

            result = await get_alerts("TX")
            assert "Unable to fetch alerts" in result
