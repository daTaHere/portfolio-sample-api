import pytest

from unittest.mock import patch
from app.services.feed_service import get_data
from app.exceptions.base_exceptions import ServiceException

DEFAULT_BASE_URL = "https://jsonplaceholder.typicode.com"
DEFAULT_ENDPOINT = "posts"
DEFAULT_START = 0
DEFAULT_LIMIT = 2


@pytest.fixture
def mock_send_request():
    with patch("app.services.feed_service.send_request") as mock_send:
        yield mock_send


@pytest.mark.asyncio
async def test_get_data_success(mock_send_request):
    endpoint = DEFAULT_ENDPOINT
    start = DEFAULT_START
    limit = DEFAULT_LIMIT
    fake_data = [{"id": 1}, {"id": 2}]
    expected_url = f"{DEFAULT_BASE_URL}/{endpoint}?_start={start}&_limit={limit}"

    mock_send_request.return_value = fake_data
    res = await get_data(endpoint, start, limit)

    mock_send_request.assert_called_once_with(expected_url)
    assert res == fake_data
    assert isinstance(res, list)
    assert len(res) == limit  # test assumes response length equals limit exactly
    assert all(isinstance(item, dict) for item in res)
    assert res[0]["id"] == start + 1
    assert res[-1]["id"] == len(res)


@pytest.mark.asyncio
async def test_get_data_response_empty_success(mock_send_request):
    endpoint = DEFAULT_ENDPOINT
    start = DEFAULT_START
    limit = 0
    fake_data = []
    expected_url = f"{DEFAULT_BASE_URL}/{endpoint}?_start={start}&_limit={limit}"

    mock_send_request.return_value = fake_data
    res = await get_data(endpoint, start, limit)

    mock_send_request.assert_called_once_with(expected_url)
    assert res == fake_data
    assert isinstance(res, list)
    assert len(res) == 0


@pytest.mark.parametrize("valid_limits", [2, 5, 8, 10])
@pytest.mark.asyncio
async def test_get_data_response_items_within_limit_success(
    mock_send_request, valid_limits
):
    endpoint = DEFAULT_ENDPOINT
    start = DEFAULT_START
    limit = 10
    # generate fake data 1 item less requested limit to test boundary or equal to 10
    # id values starting from 1 indexed
    fake_data = [
        {"id": i + 1}
        for i in range(0, valid_limits - 1 if valid_limits != 10 else valid_limits)
    ]  # return items within requested limit
    expected_url = f"{DEFAULT_BASE_URL}/{endpoint}?_start={start}&_limit={limit}"

    mock_send_request.return_value = fake_data
    res = await get_data(endpoint, start, limit)

    mock_send_request.assert_called_once_with(expected_url)
    assert res == fake_data
    assert isinstance(res, list)
    assert all(isinstance(item, dict) for item in res)
    assert len(res) <= limit
    assert res[0]["id"] == start + 1
    assert res[-1]["id"] == len(fake_data)


@pytest.mark.asyncio
async def test_get_data_response_count_mismatch_raises_service_exception(
    mock_send_request,
):
    endpoint = DEFAULT_ENDPOINT
    start = DEFAULT_START
    limit = DEFAULT_LIMIT
    fake_data = [{"id": i + 1} for i in range(0, 3)]  # 3 items returned requested 2
    expected_url = f"{DEFAULT_BASE_URL}/{endpoint}?_start={start}&_limit={limit}"

    mock_send_request.return_value = fake_data
    with patch("app.services.feed_service.logger") as mock_logger:
        with pytest.raises(ServiceException):
            await get_data(endpoint, start, limit)

    logged_error_calls = [
        call
        for call in mock_logger.error.call_args_list
        if "Response item count mismatch" in str(call)
    ]

    mock_send_request.assert_called_once_with(expected_url)
    assert len(logged_error_calls) == 1


@pytest.mark.asyncio
async def test_get_data_type_error_raises_service_exception(mock_send_request):
    """Trigger artificial TypeError/ValueError to validate exception handling in get_data."""
    endpoint = None
    start = DEFAULT_START
    limit = DEFAULT_LIMIT

    mock_send_request.side_effect = TypeError("Invalid endpoint type")
    with patch("app.services.feed_service.logger") as mock_logger:
        with pytest.raises(ServiceException):
            await get_data(endpoint, start, limit)

    logged_error_calls = [
        call
        for call in mock_logger.error.call_args_list
        if "Unexpected error in get_data" in str(call)
    ]

    assert len(logged_error_calls) == 1
