"""
Comprehensive unit tests for the request_weather function.
Covers:
- Successful data retrieval.
- Handling transport layer errors with retries.
- Correct exception raising for various failure scenarios.
- Asynchronous HTTP request mocking with respx.
"""

from unittest.mock import patch
from typing import Any, List

import pytest
import respx
import httpx

from app.services.weather.weather_fetchers import request_weather
from app.exceptions.api import (
    APIBadStatusCode,
    APIConnectionException,
    APITimeoutException,
)
from tests.utils import count_log_events


BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

TEST_RESPONSE_TEMPLATE = {
    "base": "stations",
    "clouds": {"all": 0},
    "cod": 200,
    "coord": {"lat": 34.05, "lon": -118.24},
    "dt": 1767056264,
    "id": 5368361,
    "main": {
        "feels_like": 291.45,
        "grnd_level": 1000,
        "humidity": 28,
        "pressure": 1019,
        "sea_level": 1019,
        "temp": 292.71,
        "temp_max": 294.68,
        "temp_min": 291.36,
    },
    "name": "Los Angeles",
    "sys": {
        "country": "US",
        "id": 2075946,
        "sunrise": 1767020270,
        "sunset": 1767055934,
        "type": 2,
    },
    "timezone": -28800,
    "visibility": 10000,
    "weather": [
        {"description": "clear sky", "icon": "01n", "id": 800, "main": "Clear"}
    ],
    "wind": {"deg": 338, "gust": 1.79, "speed": 0.45},
}


@pytest.fixture
def mock_cache_set():
    with patch("app.services.weather.weather_fetchers.cache_set") as mock:
        yield mock


@pytest.mark.asyncio
@respx.mock
async def test_request_weather_success(mock_cache_set, captured_logs):
    respx.get(url__regex=r"https://api\.openweathermap\.org/data/2\.5/weather.*").mock(
        return_value=httpx.Response(200, json=TEST_RESPONSE_TEMPLATE)
    )

    lat, lon = 34.05, -118.24
    data = await request_weather(lat, lon)

    log_counts = count_log_events(captured_logs, "request_weather")

    assert mock_cache_set.call_count == 2
    assert isinstance(data, dict)
    assert data["name"] == "Los Angeles"
    assert data["coord"]["lat"] == lat
    assert data["coord"]["lon"] == lon
    assert not log_counts.get("RETRIES")
    assert log_counts.get("SUCCESS")
    assert not log_counts["ERROR"]


@pytest.mark.asyncio
@respx.mock
async def test_request_weather_response_success_with_retries(
    mock_cache_set, captured_logs
):
    respx.get(url__regex=r"https://api\.openweathermap\.org/data/2\.5/weather.*").mock(
        side_effect=[
            httpx.ConnectTimeout("connection timeout"),
            httpx.TimeoutException("read timeout"),
            httpx.Response(200, json=TEST_RESPONSE_TEMPLATE),
        ]
    )

    lat, lon = 34.05, -118.24
    data = await request_weather(lat, lon)

    log_counts = count_log_events(captured_logs, "request_weather")

    assert mock_cache_set.call_count == 2
    assert isinstance(data, dict)
    assert data["name"] == "Los Angeles"
    assert data["coord"]["lat"] == lat
    assert data["coord"]["lon"] == lon
    assert log_counts.get("RETRIES") == 2
    assert log_counts.get("SUCCESS")
    assert not log_counts["ERROR"]


@pytest.mark.parametrize(
    "side_effects",
    [
        [
            httpx.ConnectTimeout("connection timeout"),
            httpx.ConnectTimeout("connection timeout"),
            httpx.ConnectTimeout("connection timeout"),
        ],
        [
            httpx.TimeoutException("read timeout"),
            httpx.TimeoutException("read timeout"),
            httpx.TimeoutException("read timeout"),
        ],
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_request_weather_raises_api_timeout_exception_exhausted_retries(
    captured_logs, side_effects: List[Exception]
):
    respx.get(url__regex=r"https://api\.openweathermap\.org/data/2\.5/weather.*").mock(
        side_effect=side_effects
    )

    lat, lon = 34.05, -118.24
    with pytest.raises(APITimeoutException):
        await request_weather(lat, lon)

    log_counts = count_log_events(captured_logs, "request_weather")

    assert log_counts.get("RETRIES") == 2
    assert not log_counts.get("SUCCESS")
    assert log_counts["ERROR"] == 1


@pytest.mark.asyncio
@respx.mock
async def test_request_weather_raises_api_connection_exception_exhausted_retries(
    mock_cache_set, captured_logs
):

    respx.get(url__regex=r"https://api\.openweathermap\.org/data/2\.5/weather.*").mock(
        side_effect=[
            httpx.ConnectError("network error"),
            httpx.ConnectError("network error"),
            httpx.ConnectError("network error"),
        ]
    )

    lat, lon = 34.05, -118.24
    with pytest.raises(APIConnectionException):
        await request_weather(lat, lon)

    log_counts = count_log_events(captured_logs, "request_weather")

    assert mock_cache_set.call_count == 0
    assert log_counts.get("RETRIES") == 2
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR")


@pytest.mark.asyncio
@respx.mock
async def test_request_weather_raises_bad_status_code_exception(
    captured_logs,
):
    mock_response = httpx.Response(500, request=httpx.Request("GET", BASE_URL))
    respx.get(url__regex=r"https://api\.openweathermap\.org/data/2\.5/weather.*").mock(
        side_effect=httpx.HTTPStatusError(
            "Bad status code", request=None, response=mock_response
        )
    )

    lat, lon = 34.05, -118.24

    with pytest.raises(APIBadStatusCode) as exc_info:
        await request_weather(lat, lon)

    log_counts = count_log_events(captured_logs, "request_weather")

    assert "Bad status code" in str(exc_info.value)
    assert not log_counts.get("RETRIES")
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR") == 1


@pytest.mark.parametrize(
    "invalid_schema",
    [[], "invalid schema", 123, None, {"unexpected": "data"}],
)
@pytest.mark.asyncio
@respx.mock
async def test_request_weather_validation_error_log_error(
    captured_logs, invalid_schema: Any
):
    respx.get(url__regex=r"https://api\.openweathermap\.org/data/2\.5/weather.*").mock(
        return_value=httpx.Response(200, json={"data": invalid_schema})
    )

    lat, lon = 34.05, -118.24
    with patch.object(httpx.Response, "json", return_value=invalid_schema):
        data = await request_weather(lat, lon)

    log_counts = count_log_events(captured_logs, "request_weather")

    assert data == {}
    assert not log_counts.get("RETRIES")
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR") == 1
    assert any("Validation Error" in log["event"] for log in captured_logs)


@pytest.mark.parametrize(
    "mock_error",
    [ValueError("Invalid data format"), TypeError("Type mismatch")],
)
@pytest.mark.asyncio
@respx.mock
async def test_request_weather_value_or_type_error_log_error(
    captured_logs, mock_error: Exception
):

    respx.get(url__regex=r"https://api\.openweathermap\.org/data/2\.5/weather.*").mock(
        return_value=httpx.Response(200, json=TEST_RESPONSE_TEMPLATE)
    )

    lat, lon = 34.05, -118.24
    with patch(
        "app.services.weather.weather_fetchers.validator.load",
        side_effect=mock_error,
    ):
        data = await request_weather(lat, lon)

    log_counts = count_log_events(captured_logs, "request_weather")

    assert data == {}
    assert not log_counts.get("RETRIES")
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR") == 1
    assert any("Value/Type Error" in log["event"] for log in captured_logs)
