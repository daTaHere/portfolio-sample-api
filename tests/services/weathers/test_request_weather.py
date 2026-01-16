"""
Comprehensive unit tests for the request_weather function.
Covers:
- Successful data retrieval.
- Handling transport layer errors with retries.
- Correct exception raising for various failure scenarios.
- Asynchronous HTTP request mocking with respx.
"""

from typing import Any, List

import pytest
import respx
import httpx
from marshmallow import ValidationError

from app.services.weather import weather_fetchers
from app.services.weather.weather_fetchers import request_weather
from app.exceptions.api import (
    APIBadStatusCode,
    APIConnectionException,
    APIJSONDecodeException,
    APITimeoutException,
    APIValidationException,
)
from tests.utils import count_log_events


BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

TEST_INPUT = {"lat": 34.05, "lon": -118.24}

TEST_RESPONSE = {
    "id": 285,
    "name": "Los Angeles",
    "coord": {"lat": 34.05, "lon": -118.24},
}


@pytest.fixture(autouse=True)
def mock_openweather_key(monkeypatch):
    monkeypatch.setattr(
        "app.services.weather.weather_fetchers.Config.OPENWEATHER_API_KEY",
        "test-api-key",
    )


@pytest.fixture(autouse=True)
def mock_OpenWeatherSchema_load(monkeypatch, request):
    if "skip_mock_OpenWeatherSchema_load" in request.keywords:
        return
    monkeypatch.setattr(
        weather_fetchers.OpenWeatherSchema,
        "load",
        lambda self, x: x,
    )


@pytest.mark.asyncio
@respx.mock
async def test_request_weather_success(captured_logs):
    mock_route = respx.get(
        url__regex=r"https://api\.openweathermap\.org/data/2\.5/weather.*"
    ).mock(return_value=httpx.Response(200, json=TEST_RESPONSE))

    data = await request_weather(**TEST_INPUT)
    log_counts = count_log_events(captured_logs, "request_weather")
    called_request = mock_route.calls.last.request

    assert called_request.url.params["lat"] == str(TEST_INPUT["lat"])
    assert called_request.url.params["lon"] == str(TEST_INPUT["lon"])
    assert data == TEST_RESPONSE
    assert not log_counts.get("RETRIES")
    assert log_counts.get("SUCCESS")
    assert not log_counts["ERROR"]


@pytest.mark.asyncio
@respx.mock
async def test_request_weather_response_success_with_retries(captured_logs):
    mock_route = respx.get(
        url__regex=r"https://api\.openweathermap\.org/data/2\.5/weather.*"
    ).mock(
        side_effect=[
            httpx.ConnectTimeout("connection timeout"),
            httpx.TimeoutException("read timeout"),
            httpx.Response(200, json=TEST_RESPONSE),
        ]
    )

    data = await request_weather(**TEST_INPUT)
    log_counts = count_log_events(captured_logs, "request_weather")
    called_request = mock_route.calls.last.request

    assert called_request.url.params["lat"] == str(TEST_INPUT["lat"])
    assert called_request.url.params["lon"] == str(TEST_INPUT["lon"])
    assert data == TEST_RESPONSE
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
    mock_route = respx.get(
        url__regex=r"https://api\.openweathermap\.org/data/2\.5/weather.*"
    ).mock(side_effect=side_effects)

    with pytest.raises(APITimeoutException):
        await request_weather(**TEST_INPUT)

    log_counts = count_log_events(captured_logs, "request_weather")
    called_request = mock_route.calls.last.request

    assert called_request.url.params["lat"] == str(TEST_INPUT["lat"])
    assert called_request.url.params["lon"] == str(TEST_INPUT["lon"])
    assert log_counts.get("RETRIES") == 2
    assert not log_counts.get("SUCCESS")
    assert log_counts["ERROR"] == 1


@pytest.mark.asyncio
@respx.mock
async def test_request_weather_raises_api_connection_exception_exhausted_retries(
    captured_logs,
):

    mock_route = respx.get(
        url__regex=r"https://api\.openweathermap\.org/data/2\.5/weather.*"
    ).mock(
        side_effect=[
            httpx.ConnectError("network error"),
            httpx.ConnectError("network error"),
            httpx.ConnectError("network error"),
        ]
    )

    with pytest.raises(APIConnectionException):
        await request_weather(**TEST_INPUT)
    log_counts = count_log_events(captured_logs, "request_weather")
    called_request = mock_route.calls.last.request

    assert called_request.url.params["lat"] == str(TEST_INPUT["lat"])
    assert called_request.url.params["lon"] == str(TEST_INPUT["lon"])
    assert log_counts.get("RETRIES") == 2
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR")


@pytest.mark.asyncio
@respx.mock
async def test_request_weather_raises_bad_status_code_exception(
    captured_logs,
):
    mock_response = httpx.Response(500, request=httpx.Request("GET", BASE_URL))
    mock_route = respx.get(
        url__regex=r"https://api\.openweathermap\.org/data/2\.5/weather.*"
    ).mock(
        side_effect=httpx.HTTPStatusError(
            "Bad status code", request=None, response=mock_response
        )
    )

    with pytest.raises(APIBadStatusCode) as exc_info:
        await request_weather(**TEST_INPUT)

    log_counts = count_log_events(captured_logs, "request_weather")
    called_request = mock_route.calls.last.request

    assert called_request.url.params["lat"] == str(TEST_INPUT["lat"])
    assert called_request.url.params["lon"] == str(TEST_INPUT["lon"])
    assert "Bad status code" in str(exc_info.value)
    assert not log_counts.get("RETRIES")
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR") == 1


@pytest.mark.parametrize(
    "invalid_response",
    [None, b"<html>not json</html>"],
)
@pytest.mark.asyncio
@respx.mock
async def test_request_weather_raises_api_bad_response_exception(
    captured_logs, invalid_response: Any
):
    mock_route = respx.get(
        url__regex=r"https://api\.openweathermap\.org/data/2\.5/weather.*"
    ).mock(return_value=httpx.Response(200, content=invalid_response))

    with pytest.raises(APIJSONDecodeException) as exc_info:
        await request_weather(**TEST_INPUT)

    log_counts = count_log_events(captured_logs, "request_weather")
    called_request = mock_route.calls.last.request

    assert called_request.url.params["lat"] == str(TEST_INPUT["lat"])
    assert called_request.url.params["lon"] == str(TEST_INPUT["lon"])
    assert not log_counts.get("RETRIES")
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR") == 1
    assert "JSONDecode Error:" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
@pytest.mark.skip_mock_OpenWeatherSchema_load
async def test_request_weather_raises_api_validation_exception(
    monkeypatch, captured_logs
):
    mock_response = {
        "id": 282828,
        "main": "Invalid Main Data",
        "name": "Los Angeles",
    }

    mock_route = respx.get(
        url__regex=r"https://api\.openweathermap\.org/data/2\.5/weather.*"
    ).mock(return_value=httpx.Response(200, json=mock_response))

    monkeypatch.setattr(
        weather_fetchers.OpenWeatherSchema,
        "load",
        lambda self, x: (_ for _ in ()).throw(ValidationError("Invalid data format")),
    )

    with pytest.raises(APIValidationException) as exc_info:
        await request_weather(**TEST_INPUT)

    log_counts = count_log_events(captured_logs, "request_weather")
    called_request = mock_route.calls.last.request

    assert called_request.url.params["lat"] == str(TEST_INPUT["lat"])
    assert called_request.url.params["lon"] == str(TEST_INPUT["lon"])
    assert not log_counts.get("RETRIES")
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR") == 1
    assert "Validation Error:" in str(exc_info.value)
