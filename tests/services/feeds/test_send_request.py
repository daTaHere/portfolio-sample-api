"""
Comprehensive unit tests for the send_request function.
Tests for the send_request function in feed_fetchers.py.
Covers:
- Successful data retrieval.
- Handling transport layer errors with retries.
- Correct exception raising for various failure scenarios.
- Asynchronous HTTP request mocking with respx.
"""

import pytest
import respx
import httpx

from unittest.mock import patch
from typing import Any
from marshmallow import ValidationError

from app.services.feeds.feed_fetchers import send_request
from app.exceptions.api import (
    APIBadStatusCode,
    APIConnectionException,
    APIJSONDecodeException,
    APITimeoutException,
    APIValidationException,
)
from app.exceptions.service import ServiceInternalException
from tests.utils import count_log_events


TEST_ENDPOINT = "https://jsonplaceholder.typicode.com/posts"

TEST_POSTS_RESPONSE = [
    {"id": 1, "userId": 10, "title": "test", "body": "lorem"},
    {"id": 2, "userId": 20, "title": "test2", "body": "ipsum"},
]


@pytest.fixture()
def mock_PostSchema_load(request):
    if "skip_mock_PostSchema_load" in request.keywords:
        return
    with patch(
        "app.services.feeds.feed_fetchers.PostSchema.load",
        side_effect=lambda x: x,
    ) as mock_load:
        yield mock_load


@pytest.mark.asyncio
@respx.mock
async def test_send_request_success(captured_logs, mock_PostSchema_load):

    url = TEST_ENDPOINT

    mock_async = respx.get(url)
    mock_async.mock(return_value=httpx.Response(200, json=TEST_POSTS_RESPONSE))

    data = await send_request(url)

    log_counts = count_log_events(captured_logs, "send_request")

    mock_PostSchema_load.assert_called_once_with(TEST_POSTS_RESPONSE)
    assert len(mock_async.calls) == 1
    assert isinstance(data, list)
    assert len(data) == 2
    assert log_counts.get("ATTEMPTS") == 1
    assert "RETRIES" not in log_counts
    assert log_counts.get("SUCCESS") == 1
    assert "ERROR" not in log_counts


@pytest.mark.asyncio
@respx.mock
async def test_send_request_success_empty_response(captured_logs, mock_PostSchema_load):

    url = TEST_ENDPOINT

    mock_async = respx.get(url)
    mock_async.mock(return_value=httpx.Response(200, json=[]))

    data = await send_request(url)

    log_counts = count_log_events(captured_logs, "send_request")

    mock_PostSchema_load.assert_called_once_with([])
    assert len(mock_async.calls) == 1
    assert isinstance(data, list)
    assert len(data) == 0
    assert log_counts.get("ATTEMPTS") == 1
    assert "RETRIES" not in log_counts
    assert log_counts.get("SUCCESS") == 1
    assert "ERROR" not in log_counts


@pytest.mark.parametrize(
    "side_effects",
    [
        [
            httpx.ConnectTimeout("connection timeout"),
            httpx.ConnectError("connection failed"),
            httpx.Response(
                200,
                json=TEST_POSTS_RESPONSE,
            ),
        ]
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_send_request_success_after_retries(
    captured_logs, mock_PostSchema_load, side_effects
):
    url = TEST_ENDPOINT

    mock_async = respx.get(url)
    mock_async.mock(side_effect=side_effects)

    await send_request(url)

    log_counts = count_log_events(captured_logs, "send_request")

    mock_PostSchema_load.assert_called_once_with(TEST_POSTS_RESPONSE)
    assert len(mock_async.calls) == 3
    assert log_counts.get("ATTEMPTS") == 3
    assert log_counts.get("RETRIES") == 2
    assert log_counts.get("SUCCESS") == 1
    assert "ERROR" not in log_counts


@pytest.mark.asyncio
@respx.mock
async def test_send_request_retry_connection_error_raises_APIConnectionException(
    captured_logs, mock_PostSchema_load
):
    url = TEST_ENDPOINT

    mock_async = respx.get(url)
    mock_async.mock(side_effect=httpx.ConnectError("connection failed"))

    with pytest.raises(APIConnectionException) as exc_info:
        await send_request(url)

    log_counts = count_log_events(captured_logs, "send_request")

    mock_PostSchema_load.assert_not_called()
    assert len(mock_async.calls) == 3
    assert log_counts.get("ATTEMPTS") == 3
    assert log_counts.get("RETRIES") == 2
    assert "SUCCESS" not in log_counts
    assert log_counts.get("ERROR") == 1
    assert "Host Connection cannot be established" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_send_request_retry_connection_timeout_raises_APITimeoutException(
    captured_logs, mock_PostSchema_load
):
    url = TEST_ENDPOINT

    mock_side_effects = [
        httpx.ConnectTimeout("connection timeout"),
        httpx.ConnectTimeout("connection timeout"),
        httpx.TimeoutException("connection timeout"),
    ]

    mock_async = respx.get(url)
    mock_async.mock(side_effect=mock_side_effects)

    with pytest.raises(APITimeoutException) as exc_info:
        await send_request(url)

    log_counts = count_log_events(captured_logs, "send_request")

    mock_PostSchema_load.assert_not_called()
    assert len(mock_async.calls) == 3
    assert log_counts.get("ATTEMPTS") == 3
    assert log_counts.get("RETRIES") == 2
    assert "SUCCESS" not in log_counts
    assert log_counts.get("ERROR") == 1
    assert "Host connection retries exhausted" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_send_request_http_status_raises_api_exception(
    captured_logs, mock_PostSchema_load
):

    url = TEST_ENDPOINT

    mock_async = respx.get(url)
    mock_async.mock(
        side_effect=httpx.HTTPStatusError(
            "Bad status code", request=None, response=httpx.Response(500)
        )
    )

    with pytest.raises(APIBadStatusCode) as exc_info:
        await send_request(url)

    log_counts = count_log_events(captured_logs, "send_request")

    mock_PostSchema_load.assert_not_called()
    assert len(mock_async.calls) == 1
    assert log_counts.get("ATTEMPTS") == 1
    assert "RETRIES" not in log_counts
    assert "SUCCESS" not in log_counts
    assert log_counts.get("ERROR") == 1
    assert "Bad status code" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize("invalid_json", [None, b"not-json"])
async def test_send_request_decoding_error_raises_api_exception(
    captured_logs, mock_PostSchema_load, invalid_json: Any
):
    url = TEST_ENDPOINT

    mock_async = respx.get(url)
    mock_async.mock(return_value=httpx.Response(200, content=invalid_json))

    with pytest.raises(APIJSONDecodeException) as exc_info:
        await send_request(url)

    log_counts = count_log_events(captured_logs, "send_request")

    mock_PostSchema_load.assert_not_called()
    assert len(mock_async.calls) == 1
    assert log_counts.get("ATTEMPTS") == 1
    assert "RETRIES" not in log_counts
    assert "SUCCESS" not in log_counts
    assert log_counts.get("ERROR") == 1
    assert "JSONDecode Error" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize("mock_error", [TypeError("bad type"), ValueError("bad value")])
async def test_send_request_internal_error_raises_ServiceInternalException(
    captured_logs, mock_PostSchema_load, mock_error: Exception
):
    url = TEST_ENDPOINT

    mock_async = respx.get(url)
    mock_async.mock(return_value=httpx.Response(200, content="mock_object"))

    with patch.object(httpx.Response, "json", side_effect=mock_error):
        with pytest.raises(ServiceInternalException) as exc_info:
            await send_request(url)

    log_counts = count_log_events(captured_logs, "send_request")

    mock_PostSchema_load.assert_not_called()
    assert log_counts.get("ATTEMPTS") == 1
    assert "RETRIES" not in log_counts
    assert "SUCCESS" not in log_counts
    assert log_counts.get("ERROR") == 1
    assert "incorrect type/value" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_send_request_validation_error_raises_APIValidationException(
    captured_logs, mock_PostSchema_load
):
    url = TEST_ENDPOINT

    mock_async = respx.get(url)
    mock_async.mock(return_value=httpx.Response(200, json=TEST_POSTS_RESPONSE))

    mock_PostSchema_load.side_effect = ValidationError("invalid data")

    with pytest.raises(APIValidationException) as exc_info:
        await send_request(url)

    log_counts = count_log_events(captured_logs, "send_request")

    mock_PostSchema_load.assert_called_once_with(TEST_POSTS_RESPONSE)
    assert len(mock_async.calls) == 1
    assert log_counts.get("ATTEMPTS") == 1
    assert "RETRIES" not in log_counts
    assert "SUCCESS" not in log_counts
    assert log_counts.get("ERROR") == 1
    assert "Validation Error:" in str(exc_info.value)
