"""
Comprehensive unit tests for weather route controller.

Covers:
- 200 success
- 404 when service returns no results
- 400 validation errors
- 408 timeout errors (APITimeoutException, TimeoutError)
- 502 bad upstream status
- 503 connection errors
- 500 grouped response errors (APIJSONDecodeException, ServiceInternalException, ValueError, TypeError)
- 500 catch-all unexpected exceptions
"""

from unittest.mock import AsyncMock, patch
import pytest

from app.exceptions.service import ServiceInternalException, ServiceValidationException
from app.routes.weather_routes import get_weather
from tests.utils import count_log_events


from app.exceptions.api import (
    APIBadStatusCode,
    APIConnectionException,
    APIJSONDecodeException,
    APITimeoutException,
)

TEST_MOCK_VALID_COORD_RESPONSE = (34.050, -118.240)
TEST_MOCK_WEATHER_RESPONSE = [{"name": "Los Angeles", "temp": 82}]


@pytest.fixture
def mock_validate_coords_key():
    with patch("app.routes.weather_routes.validate_coords_key") as mock:
        yield mock


@pytest.fixture
def mock_get_current_weather():
    with patch(
        "app.routes.weather_routes.get_current_weather", new=AsyncMock()
    ) as mock:
        yield mock


@pytest.mark.asyncio
async def test_get_weather_success_200_status(
    app, mock_validate_coords_key, mock_get_current_weather, captured_logs
):
    mock_response = TEST_MOCK_WEATHER_RESPONSE

    mock_validate_coords_key.return_value = TEST_MOCK_VALID_COORD_RESPONSE
    mock_get_current_weather.return_value = mock_response
    with app.test_request_context("/weather"):
        response_data, status_code = await get_weather()
    payload = response_data.get_json(silent=True)

    log_counts = count_log_events(captured_logs, "get_weather")

    mock_validate_coords_key.assert_called_once()
    mock_get_current_weather.assert_awaited_once_with(TEST_MOCK_VALID_COORD_RESPONSE)
    assert payload["data"] == mock_response
    assert payload["success"] is True
    assert isinstance(status_code, int)
    assert status_code == 200
    assert log_counts.get("REQUESTED") == 1
    assert log_counts.get("SUCCESS") == 1
    assert "NOT_FOUND" not in log_counts
    assert "VALIDATION_ERROR" not in log_counts
    assert "TIMEOUT_ERROR" not in log_counts
    assert "BAD_STATUS_CODE" not in log_counts
    assert "CONNECTION_ERROR" not in log_counts
    assert "RESPONSE_ERROR" not in log_counts
    assert "ERROR" not in log_counts


@pytest.mark.asyncio
async def test_get_weather_success_empty_response_404_status(
    app, mock_validate_coords_key, mock_get_current_weather, captured_logs
):
    expected = []

    mock_validate_coords_key.return_value = TEST_MOCK_VALID_COORD_RESPONSE
    mock_get_current_weather.return_value = expected
    with app.test_request_context("/weather"):
        response_data, status_code = await get_weather()
    payload = response_data.get_json(silent=True)

    log_counts = count_log_events(captured_logs, "get_weather")

    mock_validate_coords_key.assert_called_once()
    mock_get_current_weather.assert_awaited_once_with(TEST_MOCK_VALID_COORD_RESPONSE)
    assert payload["data"] == "Not Found"
    assert payload["success"] is True
    assert isinstance(status_code, int)
    assert status_code == 404
    assert log_counts.get("REQUESTED") == 1
    assert "SUCCESS" not in log_counts
    assert log_counts.get("NOT_FOUND") == 1
    assert "VALIDATION_ERROR" not in log_counts
    assert "TIMEOUT_ERROR" not in log_counts
    assert "BAD_STATUS_CODE" not in log_counts
    assert "CONNECTION_ERROR" not in log_counts
    assert "RESPONSE_ERROR" not in log_counts
    assert "ERROR" not in log_counts


@pytest.mark.asyncio
async def test_get_weather_input_validation_error_400_status(
    app, mock_validate_coords_key, mock_get_current_weather, captured_logs
):
    mock_response = ServiceValidationException(service_method="get_current_weather")

    mock_validate_coords_key.return_value = TEST_MOCK_VALID_COORD_RESPONSE
    mock_get_current_weather.side_effect = mock_response
    with app.test_request_context("/weather"):
        response_data, status_code = await get_weather()
    payload = response_data.get_json(silent=True)

    log_counts = count_log_events(captured_logs, "get_weather")

    mock_validate_coords_key.assert_called_once()
    mock_get_current_weather.assert_awaited_once_with(TEST_MOCK_VALID_COORD_RESPONSE)
    assert "error" in payload
    assert payload["success"] is False
    assert isinstance(status_code, int)
    assert status_code == 400
    assert log_counts.get("REQUESTED") == 1
    assert "SUCCESS" not in log_counts
    assert "NOT_FOUND" not in log_counts
    assert log_counts.get("VALIDATION_ERROR") == 1
    assert "TIMEOUT_ERROR" not in log_counts
    assert "BAD_STATUS_CODE" not in log_counts
    assert "CONNECTION_ERROR" not in log_counts
    assert "RESPONSE_ERROR" not in log_counts
    assert "ERROR" not in log_counts


@pytest.mark.parametrize(
    "exc",
    [
        APITimeoutException(service_name="OpenWeatherMap"),
        TimeoutError("retries exhausted"),
    ],
)
@pytest.mark.asyncio
async def test_get_weather_network_timeout_error_408_status(
    app,
    mock_validate_coords_key,
    mock_get_current_weather,
    captured_logs,
    exc: Exception,
):
    mock_response = exc

    mock_validate_coords_key.return_value = TEST_MOCK_VALID_COORD_RESPONSE
    mock_get_current_weather.side_effect = mock_response
    with app.test_request_context("/weather"):
        response_data, status_code = await get_weather()
    payload = response_data.get_json(silent=True)

    log_counts = count_log_events(captured_logs, "get_weather")

    mock_validate_coords_key.assert_called_once()
    mock_get_current_weather.assert_awaited_once_with(TEST_MOCK_VALID_COORD_RESPONSE)
    assert "error" in payload
    assert payload["success"] is False
    assert isinstance(status_code, int)
    assert status_code == 408
    assert log_counts.get("REQUESTED") == 1
    assert "SUCCESS" not in log_counts
    assert "NOT_FOUND" not in log_counts
    assert "VALIDATION_ERROR" not in log_counts
    assert log_counts.get("TIMEOUT_ERROR") == 1
    assert "BAD_STATUS_CODE" not in log_counts
    assert "CONNECTION_ERROR" not in log_counts
    assert "RESPONSE_ERROR" not in log_counts
    assert "ERROR" not in log_counts


@pytest.mark.asyncio
async def test_get_weather_bad_status_code_502_status(
    app,
    mock_validate_coords_key,
    mock_get_current_weather,
    captured_logs,
):
    mock_response = APIBadStatusCode(service_name="OpenWeatherMap")

    mock_validate_coords_key.return_value = TEST_MOCK_VALID_COORD_RESPONSE
    mock_get_current_weather.side_effect = mock_response
    with app.test_request_context("/weather"):
        response_data, status_code = await get_weather()
    payload = response_data.get_json(silent=True)

    log_counts = count_log_events(captured_logs, "get_weather")

    mock_validate_coords_key.assert_called_once()
    mock_get_current_weather.assert_awaited_once_with(TEST_MOCK_VALID_COORD_RESPONSE)
    assert "error" in payload
    assert payload["success"] is False
    assert isinstance(status_code, int)
    assert status_code == 502
    assert log_counts.get("REQUESTED") == 1
    assert "SUCCESS" not in log_counts
    assert "NOT_FOUND" not in log_counts
    assert "VALIDATION_ERROR" not in log_counts
    assert "TIMEOUT_ERROR" not in log_counts
    assert log_counts.get("BAD_STATUS_CODE") == 1
    assert "CONNECTION_ERROR" not in log_counts
    assert "RESPONSE_ERROR" not in log_counts
    assert "ERROR" not in log_counts


@pytest.mark.asyncio
async def test_get_weather_network_connection_error_503_status(
    app,
    mock_validate_coords_key,
    mock_get_current_weather,
    captured_logs,
):
    mock_response = APIConnectionException(service_name="OpenWeatherMap")

    mock_validate_coords_key.return_value = TEST_MOCK_VALID_COORD_RESPONSE
    mock_get_current_weather.side_effect = mock_response
    with app.test_request_context("/weather"):
        response_data, status_code = await get_weather()
    payload = response_data.get_json(silent=True)

    log_counts = count_log_events(captured_logs, "get_weather")

    mock_validate_coords_key.assert_called_once()
    mock_get_current_weather.assert_awaited_once_with(TEST_MOCK_VALID_COORD_RESPONSE)
    assert "error" in payload
    assert payload["success"] is False
    assert isinstance(status_code, int)
    assert status_code == 503
    assert log_counts.get("REQUESTED") == 1
    assert "SUCCESS" not in log_counts
    assert "NOT_FOUND" not in log_counts
    assert "VALIDATION_ERROR" not in log_counts
    assert "TIMEOUT_ERROR" not in log_counts
    assert "BAD_STATUS_CODE" not in log_counts
    assert log_counts.get("CONNECTION_ERROR") == 1
    assert "RESPONSE_ERROR" not in log_counts
    assert "ERROR" not in log_counts


@pytest.mark.parametrize(
    "exc",
    [
        APIJSONDecodeException(service_name="OpenWeatherMap"),
        ServiceInternalException(service_method="get_current_weather"),
        ValueError("Error: invalid value"),
        TypeError("Error: type error"),
    ],
)
@pytest.mark.asyncio
async def test_get_weather_exception_propagate_500_status(
    app,
    mock_validate_coords_key,
    mock_get_current_weather,
    captured_logs,
    exc: Exception,
):
    mock_response = exc

    mock_validate_coords_key.return_value = TEST_MOCK_VALID_COORD_RESPONSE
    mock_get_current_weather.side_effect = mock_response
    with app.test_request_context("/weather"):
        response_data, status_code = await get_weather()
    payload = response_data.get_json(silent=True)

    log_counts = count_log_events(captured_logs, "get_weather")

    mock_validate_coords_key.assert_called_once()
    mock_get_current_weather.assert_awaited_once_with(TEST_MOCK_VALID_COORD_RESPONSE)
    assert "error" in payload
    assert payload["success"] is False
    assert isinstance(status_code, int)
    assert status_code == 500
    assert log_counts.get("REQUESTED") == 1
    assert "SUCCESS" not in log_counts
    assert "NOT_FOUND" not in log_counts
    assert "VALIDATION_ERROR" not in log_counts
    assert "TIMEOUT_ERROR" not in log_counts
    assert "BAD_STATUS_CODE" not in log_counts
    assert "CONNECTION_ERROR" not in log_counts
    assert log_counts.get("RESPONSE_ERROR") == 1
    assert "ERROR" not in log_counts


@pytest.mark.parametrize(
    "exc",
    [
        AttributeError("unexpected error"),
        KeyError("unexpected error"),
        Exception("unexpected error"),
    ],
)
@pytest.mark.asyncio
async def test_get_weather_unexpected_500_status(
    app,
    mock_validate_coords_key,
    mock_get_current_weather,
    captured_logs,
    exc: Exception,
):
    mock_response = exc

    mock_validate_coords_key.side_effect = mock_response
    with app.test_request_context("/weather"):
        response_data, status_code = await get_weather()
    payload = response_data.get_json(silent=True)

    log_counts = count_log_events(captured_logs, "get_weather")

    mock_validate_coords_key.assert_called_once()
    mock_get_current_weather.assert_not_called()
    assert "error" in payload
    assert payload["success"] is False
    assert isinstance(status_code, int)
    assert status_code == 500
    assert log_counts.get("REQUESTED") == 1
    assert "SUCCESS" not in log_counts
    assert "NOT_FOUND" not in log_counts
    assert "VALIDATION_ERROR" not in log_counts
    assert "TIMEOUT_ERROR" not in log_counts
    assert "BAD_STATUS_CODE" not in log_counts
    assert "CONNECTION_ERROR" not in log_counts
    assert "RESPONSE_ERROR" not in log_counts
    assert log_counts.get("ERROR") == 1
