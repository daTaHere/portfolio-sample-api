from unittest.mock import patch
import pytest
import respx
import httpx

from app.services.feed_service import send_request
from app.exceptions.base_exceptions import APIException, ServiceException

BASE_URL = "https://jsonplaceholder.typicode.com/posts"


@pytest.mark.asyncio
@respx.mock
async def test_send_request_success():
    url = f"{BASE_URL}?_start=0&_limit=2"
    # mock a 200 JSON list response
    respx.get(url).mock(return_value=httpx.Response(200, json=[{"id": 1}, {"id": 2}]))

    data = await send_request(url)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["id"] == 1


@pytest.mark.asyncio
@respx.mock
async def test_send_request_empty_response_success():
    url = f"{BASE_URL}?_start=0&_limit=0"
    # mock a 200 JSON list response
    respx.get(url).mock(return_value=httpx.Response(200, json=[]))

    data = await send_request(url)
    assert isinstance(data, list)
    assert len(data) == 0
    assert data == []


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize("bad_json", [123, True, "string", {"key": "value"}])
async def test_send_request_unexpected_json_type_raise_service_exception(bad_json):
    url = BASE_URL
    # mock a 200 response with bad JSON type
    respx.get(url).mock(return_value=httpx.Response(200, json=bad_json))

    with pytest.raises(ServiceException):
        await send_request(url)


@pytest.mark.asyncio
@respx.mock
async def test_send_request_null_response_raises_service_exception():
    url = BASE_URL
    # mock a 200 response with null JSON
    respx.get(url).mock(return_value=httpx.Response(200, content=b"null"))

    with pytest.raises(ServiceException):
        await send_request(url)


@pytest.mark.asyncio
@respx.mock
async def test_send_request_decoding_error_raises_api_exception():
    url = BASE_URL
    # simulate decoding error
    respx.get(url).mock(side_effect=httpx.DecodingError("invalid json response"))

    with pytest.raises(APIException):
        await send_request(url)


@pytest.mark.asyncio
@respx.mock
async def test_send_request_http_status_raises_api_exception():
    url = BASE_URL
    # mock a 500
    respx.get(url).mock(return_value=httpx.Response(500, json={"error": "server"}))

    with pytest.raises(APIException):
        await send_request(url)


@pytest.mark.asyncio
@respx.mock
async def test_send_request_network_error_raises_api_exception():
    url = BASE_URL
    # simulate network/connect error
    route = respx.get(url).mock(side_effect=httpx.ConnectError("connection failed"))

    with pytest.raises(APIException):
        await send_request(url)

    assert len(route.calls) == 3  # Ensure 3 retries were attempted


@pytest.mark.asyncio
@respx.mock
async def test_send_request_decoding_error_raises_api_exception():
    url = BASE_URL
    # simulate decoding error
    respx.get(url).mock(side_effect=httpx.Response(500, content=b"invalid json"))

    with pytest.raises(APIException):
        await send_request(url)


@pytest.mark.asyncio
@respx.mock
async def test_send_request_retry_connection_timeout_raises_api_exception(caplog):
    url = BASE_URL
    # simulate network/connect timeout error
    route = respx.get(url).mock(side_effect=httpx.ConnectTimeout("connection timeout"))
    with patch("app.services.feed_service.logger") as mock_logger:
        with pytest.raises(APIException):
            await send_request(url)

    assert len(route.calls) == 3  # Ensure 3 retries were attempted

    # Inspect logger calls
    retry_logs = [
        call
        for call in mock_logger.warning.call_args_list
        if "Request attempt" in call.args[0]
    ]
    final_error_logs = [
        call
        for call in mock_logger.error.call_args_list
        if "Request failed" in call.args[0]
    ]

    assert len(retry_logs) == 2  # 3 retries before the last attempt
    assert len(final_error_logs) == 1  # final failure logged
