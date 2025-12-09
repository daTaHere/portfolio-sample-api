import pytest

from unittest.mock import MagicMock, patch
from typing import Any, Dict, Generator, List
from tests.utils import count_log_events

from app.services.feeds.feed_validators import get_data
from app.exceptions.base import ServiceException

DEFAULT_BASE_URL = "https://jsonplaceholder.typicode.com"
DEFAULT_ENDPOINT = "posts"
DEFAULT_START = 0
DEFAULT_LIMIT = 2


@pytest.fixture
def mock_send_request() -> Generator[MagicMock, None, None]:
    with patch("app.services.feeds.feed_validators.send_request") as mock_send:
        yield mock_send


@pytest.mark.parametrize(
    "start, limit, test_data",
    [
        (
            DEFAULT_START,
            DEFAULT_LIMIT,
            [{"id": num + 1} for num in range(0, DEFAULT_LIMIT)],
        ),
        (DEFAULT_START, 5, [{"id": num + 1} for num in range(0, 5)]),
        (
            DEFAULT_START,
            10,
            [{"id": num + 1} for num in range(0, 10)],
        ),
    ],
)
@pytest.mark.asyncio
async def test_get_data_success(
    captured_logs,
    mock_send_request: MagicMock,
    start: int,
    limit: int,
    test_data: List[Dict[str, Any]],
):
    endpoint = DEFAULT_ENDPOINT
    expected_url = f"{DEFAULT_BASE_URL}/{endpoint}?_start={start}&_limit={limit}"

    mock_send_request.return_value = test_data
    res = await get_data(endpoint, start, limit)

    mock_send_request.assert_called_once_with(expected_url)
    log_counts = count_log_events(captured_logs, "get_data")

    assert res == test_data
    assert isinstance(res, list)
    assert len(res) == limit  # test assumes response length equals limit exactly
    assert all(isinstance(item, dict) for item in res)
    assert res[0]["id"] == start + 1
    assert res[-1]["id"] == len(res)
    assert log_counts.get("ENDPOINT_URL")
    assert log_counts.get("REQUEST_ATTEMPT")
    assert log_counts.get("SUCCESS")
    assert not log_counts.get("ERROR")


@pytest.mark.asyncio
async def test_get_data_response_empty_success(
    captured_logs, mock_send_request: MagicMock
):
    endpoint = DEFAULT_ENDPOINT
    start = DEFAULT_START
    limit = 0
    fake_data = []
    expected_url = f"{DEFAULT_BASE_URL}/{endpoint}?_start={start}&_limit={limit}"

    mock_send_request.return_value = fake_data
    res = await get_data(endpoint, start, limit)

    log_counts = count_log_events(captured_logs, "get_data")

    mock_send_request.assert_called_once_with(expected_url)
    assert res == fake_data
    assert isinstance(res, list)
    assert len(res) == 0
    assert log_counts.get("ENDPOINT_URL")
    assert log_counts.get("REQUEST_ATTEMPT")
    assert log_counts.get("SUCCESS")
    assert not log_counts.get("ERROR")


@pytest.mark.parametrize(
    "expected_count, test_data",
    [
        (1, [{"id": num} for num in range(1, 2)]),
        (5, [{"id": num} for num in range(1, 6)]),
        (8, [{"id": num} for num in range(1, 9)]),
        (10, [{"id": num} for num in range(1, 11)]),
    ],
)
@pytest.mark.asyncio
async def test_get_data_response_items_within_limit_success(
    captured_logs,
    mock_send_request: MagicMock,
    expected_count: int,
    test_data: List[Dict[str, Any]],
):
    endpoint = DEFAULT_ENDPOINT
    start = DEFAULT_START
    limit = 10
    expected_url = f"{DEFAULT_BASE_URL}/{endpoint}?_start={start}&_limit={limit}"

    mock_send_request.return_value = test_data
    res = await get_data(endpoint, start, limit)

    log_counts = count_log_events(captured_logs, "get_data")

    mock_send_request.assert_called_once_with(expected_url)
    assert len(res) == expected_count
    assert len(res) <= limit
    assert res == test_data
    assert isinstance(res, list)
    assert all(isinstance(item, dict) for item in res)
    assert res[0]["id"] == start + 1
    assert res[-1]["id"] == len(test_data)
    assert log_counts.get("ENDPOINT_URL")
    assert log_counts.get("REQUEST_ATTEMPT")
    assert log_counts.get("SUCCESS")
    assert not log_counts.get("ERROR")


@pytest.mark.parametrize(
    "test_limit, test_data",
    [
        (
            DEFAULT_LIMIT,
            [{"id": num} for num in range(1, 4)],
        ),
        (5, [{"id": num} for num in range(1, 7)]),
        (10, [{"id": num} for num in range(1, 12)]),
    ],
)
@pytest.mark.asyncio
async def test_get_data_response_count_mismatch_raises_service_exception(
    captured_logs,
    mock_send_request: MagicMock,
    test_limit: int,
    test_data: List[Dict[str, Any]],
):
    endpoint = DEFAULT_ENDPOINT
    start = DEFAULT_START
    limit = test_limit
    expected_url = f"{DEFAULT_BASE_URL}/{endpoint}?_start={start}&_limit={limit}"

    mock_send_request.return_value = test_data
    with pytest.raises(ServiceException) as exc_info:
        await get_data(endpoint, start, limit)

    log_counts = count_log_events(captured_logs, "get_data")

    mock_send_request.assert_called_once_with(expected_url)
    assert "Internal Server Error Received:" in str(exc_info.value)
    assert len(mock_send_request.return_value) > limit
    assert log_counts.get("ENDPOINT_URL")
    assert log_counts.get("REQUEST_ATTEMPT")
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR")


@pytest.mark.parametrize(
    "test_data",
    [
        "This is a string, not a list",
        1234,
        {"id": 1, "name": "Test"},
        12.34,
        {1, 2, 3},
    ],
)
@pytest.mark.asyncio
async def test_get_data_type_error_raises_service_exception(
    captured_logs,
    mock_send_request: MagicMock,
    test_data: Any,
):
    """Trigger artificial TypeError/ValueError to validate exception handling in get_data."""
    endpoint = DEFAULT_ENDPOINT
    start = DEFAULT_START
    limit = DEFAULT_LIMIT

    mock_send_request.return_value = test_data
    with pytest.raises(ServiceException) as exc_info:
        await get_data(endpoint, start, limit)

    log_counts = count_log_events(captured_logs, "get_data")

    assert f"Internal Server Error: expected List" in str(exc_info.value)
    assert log_counts.get("ENDPOINT_URL")
    assert log_counts.get("REQUEST_ATTEMPT")
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR")
