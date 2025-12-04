import pytest
import respx
import httpx
from unittest.mock import patch

from typing import Any

from app.services.feed_service import send_request
from app.exceptions.base import APIException, ServiceException
from tests.utils import count_log_events


BASE_URL = "https://jsonplaceholder.typicode.com/posts"


@pytest.mark.asyncio
@respx.mock
async def test_send_request_success(captured_logs):
    url = f"{BASE_URL}?_start=0&_limit=2"
    # mock a 200 JSON list response
    respx.get(url).mock(return_value=httpx.Response(200, json=[{"id": 1}, {"id": 2}]))
    data = await send_request(url)

    log_counts = count_log_events(captured_logs, "send_request")

    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[-1]["id"] == 2
    assert log_counts.get("ATTEMPTS")
    assert not log_counts.get("RETRIES")
    assert log_counts.get("SUCCESS")
    assert not log_counts.get("ERROR")


@pytest.mark.asyncio
@respx.mock
async def test_send_request_empty_response_success(captured_logs):
    url = f"{BASE_URL}?_start=0&_limit=0"
    # mock a 200 JSON empty list response
    respx.get(url).mock(return_value=httpx.Response(200, json=[]))

    data = await send_request(url)

    log_counts = count_log_events(captured_logs, "send_request")
    assert isinstance(data, list)
    assert len(data) == 0
    assert log_counts.get("ATTEMPTS")
    assert not log_counts.get("RETRIES")
    assert log_counts.get("SUCCESS")
    assert not log_counts.get("ERROR")


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize("bad_json", [123, True, "string", {"key": "value"}])
async def test_send_request_unexpected_json_type_raises_service_exception(
    captured_logs,
    bad_json: Any,
):
    url = BASE_URL
    # mock a 200 response with bad JSON type
    respx.get(url).mock(return_value=httpx.Response(200, json=bad_json))

    with pytest.raises(ServiceException):
        await send_request(url)

    log_counts = count_log_events(captured_logs, "send_request")

    assert log_counts.get("ATTEMPTS")
    assert not log_counts.get("RETRIES")
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR")


@pytest.mark.asyncio
@respx.mock
async def test_send_request_null_response_raises_service_exception(captured_logs):
    url = BASE_URL
    # mock a 200 response with null JSON
    respx.get(url).mock(return_value=httpx.Response(200, content=b"null"))

    with pytest.raises(ServiceException):
        await send_request(url)

    log_counts = count_log_events(captured_logs, "send_request")

    assert log_counts.get("ATTEMPTS")
    assert not log_counts.get("RETRIES")
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR")


@pytest.mark.asyncio
@respx.mock
async def test_send_request_decoding_error_raises_api_exception(captured_logs):
    url = BASE_URL

    respx.get(url).mock(return_value=httpx.Response(200, content=b"not-json"))

    # Mock json() to raise DecodingError
    with patch.object(
        httpx.Response, "json", side_effect=httpx.DecodingError("invalid json response")
    ):
        with pytest.raises(APIException) as exc_info:
            await send_request(url)

    log_counts = count_log_events(captured_logs, "send_request")

    assert f"External API Error: Invalid JSON response." in str(exc_info.value)
    assert log_counts.get("ATTEMPTS")
    assert not log_counts.get("RETRIES")
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR")


@pytest.mark.asyncio
@respx.mock
async def test_send_request_http_status_raises_api_exception(captured_logs):
    url = BASE_URL
    # mock a 500
    respx.get(url).mock(return_value=httpx.Response(500, json={"error": "server"}))

    with pytest.raises(APIException) as exc_info:
        await send_request(url)

    log_counts = count_log_events(captured_logs, "send_request")

    assert log_counts.get("ATTEMPTS") == 1
    assert not log_counts.get("RETRIES")
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR")


@pytest.mark.asyncio
@respx.mock
async def test_send_request_network_error_raises_api_exception(captured_logs):
    url = BASE_URL
    # simulate network/connect error
    respx.get(url).mock(side_effect=httpx.ConnectError("connection failed"))

    with pytest.raises(APIException) as exc_info:
        await send_request(url)

    log_counts = count_log_events(captured_logs, "send_request")

    assert f"External API Error: Unreachable" in str(exc_info.value)
    assert log_counts.get("ATTEMPTS") == 3
    assert log_counts.get("RETRIES") == 2
    assert log_counts.get("ERROR")
    assert not log_counts.get("SUCCESS")


@pytest.mark.asyncio
@respx.mock
async def test_send_request_retry_connection_timeout_raises_api_exception(
    captured_logs,
):
    url = BASE_URL
    # simulate network/connect timeout error
    respx.get(url).mock(side_effect=httpx.ConnectTimeout("connection timeout"))

    with pytest.raises(APIException) as exc_info:
        await send_request(url)

    log_counts = count_log_events(captured_logs, "send_request")

    assert f"External API Error: Unreachable" in str(exc_info.value)
    assert log_counts.get("ATTEMPTS") == 3
    assert log_counts.get("RETRIES") == 2
    assert log_counts.get("ERROR")
    assert not log_counts.get("SUCCESS")


@pytest.mark.parametrize(
    "side_effects",
    [
        [
            httpx.ConnectTimeout("connection timeout"),
            httpx.ConnectTimeout("connection timeout"),
            httpx.Response(200, json=[{"id": 1}, {"id": 2}]),
        ]
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_send_request_retry_and_response_success(captured_logs, side_effects):
    url = f"{BASE_URL}?_start=0&_limit=2"
    # mock a 200 JSON list response

    respx.get(url).mock(side_effect=side_effects)
    data = await send_request(url)

    log_counts = count_log_events(captured_logs, "send_request")

    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[-1]["id"] == 2
    assert log_counts.get("ATTEMPTS") == 3
    assert log_counts.get("RETRIES") == 2
    assert not log_counts.get("ERROR")
    assert log_counts.get("SUCCESS")
