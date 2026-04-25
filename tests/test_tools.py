"""Unit tests for tools.py — get_coordinates and get_historical_weather."""

from unittest.mock import MagicMock, patch

import pytest

from tools import get_coordinates, get_historical_weather


# ---------------------------------------------------------------------------
# get_coordinates
# ---------------------------------------------------------------------------


class TestGetCoordinates:
    def test_returns_lat_lon_name_country_on_success(self):
        # Arrange
        mock_result = {
            "results": [
                {
                    "latitude": 35.6762,
                    "longitude": 139.6503,
                    "name": "東京",
                    "country": "日本",
                    "elevation": 40.0,
                }
            ]
        }
        mock_response = MagicMock()
        mock_response.json.return_value = mock_result

        # Act
        with patch("tools.requests.get", return_value=mock_response) as mock_get:
            result = get_coordinates("東京")

        # Assert
        mock_get.assert_called_once()
        assert result["latitude"] == 35.6762
        assert result["longitude"] == 139.6503
        assert result["name"] == "東京"
        assert result["country"] == "日本"
        assert "error" not in result

    def test_returns_error_when_results_empty(self):
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}

        # Act
        with patch("tools.requests.get", return_value=mock_response):
            result = get_coordinates("存在しない地点XYZ")

        # Assert
        assert "error" in result
        assert "存在しない地点XYZ" in result["error"]

    def test_returns_error_when_results_key_missing(self):
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {}

        # Act
        with patch("tools.requests.get", return_value=mock_response):
            result = get_coordinates("不明")

        # Assert
        assert "error" in result

    def test_returns_error_on_request_exception(self):
        import requests as req_lib

        # Act
        with patch("tools.requests.get", side_effect=req_lib.RequestException("timeout")):
            result = get_coordinates("東京")

        # Assert
        assert "error" in result
        assert "timeout" in result["error"]

    def test_country_defaults_to_empty_string_when_missing(self):
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"latitude": 0.0, "longitude": 0.0, "name": "Unknown"}
                # "country" key absent
            ]
        }

        # Act
        with patch("tools.requests.get", return_value=mock_response):
            result = get_coordinates("Unknown")

        # Assert
        assert result["country"] == ""

    def test_passes_correct_query_params(self):
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{"latitude": 48.8566, "longitude": 2.3522, "name": "Paris", "country": "France"}]
        }

        # Act
        with patch("tools.requests.get", return_value=mock_response) as mock_get:
            get_coordinates("Paris")

        # Assert
        _, kwargs = mock_get.call_args
        params = kwargs["params"]
        assert params["name"] == "Paris"
        assert params["count"] == 1
        assert params["language"] == "ja"


# ---------------------------------------------------------------------------
# get_historical_weather
# ---------------------------------------------------------------------------


def _make_hourly_response(temps, humidities):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "hourly": {
            "time": [f"2023-07-15T{h:02d}:00" for h in range(len(temps))],
            "temperature_2m": temps,
            "relative_humidity_2m": humidities,
        }
    }
    return mock_response


class TestGetHistoricalWeather:
    LAT, LON, DATE = 35.6762, 139.6503, "2023-07-15"

    def test_returns_aggregated_stats_on_success(self):
        # Arrange
        temps = [20.0, 22.0, 24.0, 26.0]
        humids = [60.0, 65.0, 70.0, 55.0]
        mock_response = _make_hourly_response(temps, humids)

        # Act
        with patch("tools.requests.get", return_value=mock_response):
            result = get_historical_weather(self.LAT, self.LON, self.DATE)

        # Assert
        assert result["date"] == self.DATE
        assert result["avg_temperature_celsius"] == 23.0
        assert result["min_temperature_celsius"] == 20.0
        assert result["max_temperature_celsius"] == 26.0
        assert result["avg_humidity_percent"] == 62.5
        assert "error" not in result

    def test_filters_none_values_from_temps(self):
        # Arrange
        temps = [20.0, None, 30.0]
        humids = [60.0, None, 80.0]
        mock_response = _make_hourly_response(temps, humids)

        # Act
        with patch("tools.requests.get", return_value=mock_response):
            result = get_historical_weather(self.LAT, self.LON, self.DATE)

        # Assert
        assert result["avg_temperature_celsius"] == 25.0
        assert result["min_temperature_celsius"] == 20.0
        assert result["max_temperature_celsius"] == 30.0
        assert result["avg_humidity_percent"] == 70.0

    def test_returns_error_when_all_temps_none(self):
        # Arrange
        mock_response = _make_hourly_response([None, None], [None, None])

        # Act
        with patch("tools.requests.get", return_value=mock_response):
            result = get_historical_weather(self.LAT, self.LON, self.DATE)

        # Assert
        assert "error" in result

    def test_returns_error_when_hourly_temps_empty(self):
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"hourly": {"temperature_2m": [], "relative_humidity_2m": []}}

        # Act
        with patch("tools.requests.get", return_value=mock_response):
            result = get_historical_weather(self.LAT, self.LON, self.DATE)

        # Assert
        assert "error" in result

    def test_returns_error_when_api_returns_error_key(self):
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": True, "reason": "日付が範囲外です"}

        # Act
        with patch("tools.requests.get", return_value=mock_response):
            result = get_historical_weather(self.LAT, self.LON, self.DATE)

        # Assert
        assert "error" in result
        assert "日付が範囲外です" in result["error"]

    def test_returns_error_on_request_exception(self):
        import requests as req_lib

        # Act
        with patch("tools.requests.get", side_effect=req_lib.RequestException("connection error")):
            result = get_historical_weather(self.LAT, self.LON, self.DATE)

        # Assert
        assert "error" in result
        assert "connection error" in result["error"]

    def test_avg_humidity_is_none_when_humidities_all_none(self):
        # Arrange
        mock_response = _make_hourly_response([20.0, 25.0], [None, None])

        # Act
        with patch("tools.requests.get", return_value=mock_response):
            result = get_historical_weather(self.LAT, self.LON, self.DATE)

        # Assert
        assert result["avg_humidity_percent"] is None

    def test_passes_correct_query_params(self):
        # Arrange
        mock_response = _make_hourly_response([20.0], [60.0])

        # Act
        with patch("tools.requests.get", return_value=mock_response) as mock_get:
            get_historical_weather(self.LAT, self.LON, self.DATE)

        # Assert
        _, kwargs = mock_get.call_args
        params = kwargs["params"]
        assert params["latitude"] == self.LAT
        assert params["longitude"] == self.LON
        assert params["start_date"] == self.DATE
        assert params["end_date"] == self.DATE
        assert "temperature_2m" in params["hourly"]
        assert "relative_humidity_2m" in params["hourly"]
