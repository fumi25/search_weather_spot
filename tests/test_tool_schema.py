"""Unit tests for tool_schema.py — TOOLS structure validation."""

from tool_schema import TOOLS


class TestToolsSchema:
    def test_tools_is_list(self):
        assert isinstance(TOOLS, list)

    def test_tools_has_two_entries(self):
        assert len(TOOLS) == 2

    def test_all_entries_have_type_function(self):
        for tool in TOOLS:
            assert tool.get("type") == "function"

    def test_get_coordinates_schema_present(self):
        names = [t["function"]["name"] for t in TOOLS]
        assert "get_coordinates" in names

    def test_get_historical_weather_schema_present(self):
        names = [t["function"]["name"] for t in TOOLS]
        assert "get_historical_weather" in names

    def test_get_coordinates_has_required_place_param(self):
        schema = next(t for t in TOOLS if t["function"]["name"] == "get_coordinates")
        params = schema["function"]["parameters"]
        assert "place" in params["properties"]
        assert "place" in params["required"]

    def test_get_historical_weather_has_required_params(self):
        schema = next(t for t in TOOLS if t["function"]["name"] == "get_historical_weather")
        params = schema["function"]["parameters"]
        required = params["required"]
        for field in ("latitude", "longitude", "date"):
            assert field in params["properties"], f"{field} must be in properties"
            assert field in required, f"{field} must be required"

    def test_latitude_and_longitude_are_number_type(self):
        schema = next(t for t in TOOLS if t["function"]["name"] == "get_historical_weather")
        props = schema["function"]["parameters"]["properties"]
        assert props["latitude"]["type"] == "number"
        assert props["longitude"]["type"] == "number"

    def test_date_is_string_type(self):
        schema = next(t for t in TOOLS if t["function"]["name"] == "get_historical_weather")
        props = schema["function"]["parameters"]["properties"]
        assert props["date"]["type"] == "string"

    def test_all_functions_have_description(self):
        for tool in TOOLS:
            assert tool["function"].get("description"), f"{tool['function']['name']} must have a description"
