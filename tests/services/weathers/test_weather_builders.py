"""
Comprehensive unit tests for the request_weather function.
Covers:
- Successful data retrieval.
- Handling transport layer errors with retries.
- Correct exception raising for various failure scenarios.
- Asynchronous HTTP request mocking with respx.
"""

import pytest
from unittest.mock import patch

from marshmallow import ValidationError

from app.services.weather import weather_builders
from app.services.weather.weather_builders import (
    create_fetch_list,
    process_from_cache,
    create_weather_model,
)
from app.exceptions.service import ServiceInternalException, ServiceValidationException

from tests.utils import count_log_events

TEST_NEW_COORDS = (8.0, 8.0)
TEST_DEFAULT_COORDS = (2.0, 2.0)

DEFAULT_TEST_COORDS = [
    (1.0, 1.0),
    (2.0, 2.0),
    (3.0, 3.0),
]

MOCK_TEST_DATA = [
    {"id": 1, "name": "CityA", "coord": {"lat": 1.0, "lon": 1.0}},
    {"id": 2, "name": "CityB", "coord": {"lat": 2.0, "lon": 2.0}},
    {"id": 3, "name": "CityC", "coord": {"lat": 3.0, "lon": 3.0}},
]


class TestCreateFetchList:

    @pytest.fixture(autouse=True)
    def mock_default_coords(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.weather.weather_builders.DEFAULT_CITIES",
            DEFAULT_TEST_COORDS,
        )

    def test_create_fetch_list_success_with_new_coords(self, captured_logs):

        fetch_list = create_fetch_list(TEST_NEW_COORDS)
        log_counts = count_log_events(captured_logs, "create_fetch_list")

        assert len(fetch_list) == 3
        assert fetch_list[0] == TEST_NEW_COORDS
        assert fetch_list[-1] == DEFAULT_TEST_COORDS[-2]
        assert log_counts.get("INFO") == 1
        assert not log_counts.get("GET_DEFAULT_CITIES")
        assert log_counts.get("PREPEND_USER_COORDS") == 1
        assert not log_counts.get("SWAP_LOCATION_ORDER")
        assert log_counts.get("SUCCESS") == 1

    def test_create_fetch_list_with_default_coords(self, captured_logs):

        fetch_list = create_fetch_list(TEST_DEFAULT_COORDS)
        log_counts = count_log_events(captured_logs, "create_fetch_list")

        assert len(fetch_list) == 3
        assert fetch_list[0] == TEST_DEFAULT_COORDS
        assert fetch_list[1] == DEFAULT_TEST_COORDS[0]
        assert log_counts.get("INFO") == 1
        assert not log_counts.get("GET_DEFAULT_CITIES")
        assert not log_counts.get("PREPEND_USER_COORDS")
        assert log_counts.get("SWAP_LOCATION_ORDER")
        assert log_counts.get("SUCCESS") == 1

    def test_create_fetch_list_with_no_coords(self, captured_logs):

        fetch_list = create_fetch_list(None)
        log_counts = count_log_events(captured_logs, "create_fetch_list")

        assert len(fetch_list) == 3
        assert fetch_list == DEFAULT_TEST_COORDS
        assert log_counts.get("INFO") == 1
        assert log_counts.get("GET_DEFAULT_CITIES")
        assert not log_counts.get("PREPEND_USER_COORDS")
        assert not log_counts.get("SWAP_LOCATION_ORDER")
        assert not log_counts.get("SUCCESS")


class TestProcessFromCache:

    @pytest.fixture(autouse=True)
    def mock_default_coords(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.weather.weather_builders.DEFAULT_CITIES",
            DEFAULT_TEST_COORDS,
        )

    def test_process_from_cache_all_miss(self, monkeypatch, captured_logs):

        monkeypatch.setattr(
            weather_builders.WeatherSchema,
            "load",
            lambda self, x: x,
        )
        with patch(
            "app.services.weather.weather_builders.cache_get", return_value=None
        ):
            cached_data, missing_coords = process_from_cache(DEFAULT_TEST_COORDS)

        log_counts = count_log_events(captured_logs, "process_from_cache")

        assert missing_coords == [
            (i, coord) for i, coord in enumerate(DEFAULT_TEST_COORDS)
        ]
        assert all(isinstance(item, type(None)) for item in cached_data)
        assert log_counts.get("PROCESS_FROM_CACHE") == 1
        assert log_counts.get("SUCCESS") == 1
        assert log_counts.get("WEATHER_COORDS_CACHED") == 1
        assert not log_counts.get("CACHE_DESERIALIZATION_ERROR")

    def test_process_from_cache_partial_hit(self, monkeypatch, captured_logs):

        def mock_cache_get(key: str):
            cache_map = {
                "1.0,1.0": MOCK_TEST_DATA[0],
                "2.0,2.0": MOCK_TEST_DATA[1],
            }
            return cache_map.get(key, None)

        monkeypatch.setattr(
            weather_builders.WeatherSchema,
            "load",
            lambda self, x: x,
        )

        with patch(
            "app.services.weather.weather_builders.cache_get",
            side_effect=mock_cache_get,
        ):
            cached_data, missing_coords = process_from_cache(DEFAULT_TEST_COORDS)

        log_counts = count_log_events(captured_logs, "process_from_cache")

        assert len(missing_coords) == 1
        assert missing_coords[0] == (2, DEFAULT_TEST_COORDS[2])
        assert cached_data[:2] == MOCK_TEST_DATA[:2]
        assert log_counts.get("PROCESS_FROM_CACHE") == 1
        assert log_counts.get("SUCCESS") == 1
        assert log_counts.get("WEATHER_COORDS_CACHED") == 1
        assert not log_counts.get("CACHE_DESERIALIZATION_ERROR")

    @pytest.fixture
    def schema_load_side_effect(self):
        """Creates a side effect function for raising ValidationError on 2nd call."""
        count = {"n": 0}

        def _load(self, x):
            count["n"] += 1
            if count["n"] == 1:
                return x
            raise ValidationError("boom")

        return _load

    def test_process_from_cache_partial_hit_with_validation_exception(
        self, monkeypatch, schema_load_side_effect, captured_logs
    ):

        def mock_cache_get(key: str):
            cache_map = {
                "1.0,1.0": MOCK_TEST_DATA[0],
                "2.0,2.0": MOCK_TEST_DATA[1],
            }
            return cache_map.get(key, None)

        monkeypatch.setattr(
            weather_builders.WeatherSchema,
            "load",
            schema_load_side_effect,
        )

        with patch(
            "app.services.weather.weather_builders.cache_get",
            side_effect=mock_cache_get,
        ):
            cached_data, missing_coords = process_from_cache(DEFAULT_TEST_COORDS)

        log_counts = count_log_events(captured_logs, "process_from_cache")

        assert len(missing_coords) == 2
        assert missing_coords[0] == (1, DEFAULT_TEST_COORDS[1])
        assert missing_coords[1] == (2, DEFAULT_TEST_COORDS[2])
        assert cached_data[:1] == MOCK_TEST_DATA[:1]
        assert log_counts.get("PROCESS_FROM_CACHE") == 1
        assert log_counts.get("SUCCESS") == 1
        assert log_counts.get("WEATHER_COORDS_CACHED") == 1
        assert log_counts.get("CACHE_DESERIALIZATION_ERROR")


class TestCreateWeatherModel:

    @pytest.fixture
    def mock_cache_set(self):
        with patch("app.services.weather.weather_builders.cache_set") as mock:
            yield mock

    @pytest.fixture
    def mock_weather_schema(self):
        with patch("app.services.weather.weather_builders.WeatherSchema") as mock:
            yield mock

    @pytest.fixture
    def mock_weather_model(self):
        with patch("app.services.weather.weather_builders.WeatherModel") as mock:
            yield mock

    @pytest.fixture
    def fake_weather_model_cls(self):
        """Returns a coord attribute for the MockWeatherModel"""

        class MockWeatherModel:
            def __init__(self, data):
                self.coord = data["coord"]

        return MockWeatherModel

    def test_create_weather_model_success(
        self,
        mock_weather_model,
        fake_weather_model_cls,
        mock_weather_schema,
        mock_cache_set,
        captured_logs,
    ):

        test_data = MOCK_TEST_DATA

        mock_weather_model.side_effect = fake_weather_model_cls
        mock_weather_schema.return_value.dump.side_effect = lambda x: x
        mock_cache_set.return_value = None
        weather_models = create_weather_model(test_data)

        log_counts = count_log_events(captured_logs, "create_weather_model")

        assert mock_cache_set.call_count == len(test_data)
        assert len(weather_models) == len(test_data)
        assert log_counts.get("INFO") == 1
        assert log_counts.get("SUCCESS") == 1
        assert not log_counts.get("ERROR")

    @pytest.mark.parametrize(
        "mock_error",
        [
            ValueError("Invalid data"),
            AttributeError("Invalid data"),
            TypeError("Invalid data"),
        ],
    )
    def test_create_weather_model_raise_service_internal_exception(
        self,
        mock_weather_model,
        mock_weather_schema,
        mock_cache_set,
        captured_logs,
        mock_error: Exception,
    ):

        test_data = MOCK_TEST_DATA
        mock_weather_model.side_effect = mock_error
        with pytest.raises(ServiceInternalException) as exc_info:
            create_weather_model(test_data)

        log_counts = count_log_events(captured_logs, "create_weather_model")

        mock_weather_schema.return_value.dump.assert_not_called()
        mock_cache_set.assert_not_called()
        assert log_counts.get("INFO") == 1
        assert log_counts.get("ERROR") == 1
        assert not log_counts.get("SUCCESS")
        assert "Internal Error:" in str(exc_info.value)

    def test_create_weather_model_raise_service_validation_exception(
        self,
        mock_weather_model,
        fake_weather_model_cls,
        mock_weather_schema,
        mock_cache_set,
        captured_logs,
    ):

        test_data = MOCK_TEST_DATA

        mock_weather_model.side_effect = fake_weather_model_cls
        mock_weather_schema.return_value.dump.side_effect = ValidationError(
            "Invalid data"
        )
        with pytest.raises(ServiceValidationException) as exc_info:
            create_weather_model(test_data)

        log_counts = count_log_events(captured_logs, "create_weather_model")

        mock_cache_set.assert_not_called()
        assert mock_weather_model.call_count == 1
        assert mock_weather_schema.return_value.dump.call_count == 1
        assert log_counts.get("INFO") == 1
        assert log_counts.get("ERROR") == 1
        assert not log_counts.get("SUCCESS")
        assert "Validation Error:" in str(exc_info.value)
