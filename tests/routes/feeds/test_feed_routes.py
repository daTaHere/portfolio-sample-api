"""
Unit tests for user service and routes.
"""

import pytest
import asyncio

from unittest.mock import AsyncMock, patch
from typing import Any, List, Dict
from tests.utils import count_log_events

from app.routes.feed_routes import get_feeds
from app.exceptions.base import APIException, ServiceException


@pytest.fixture
def mock_get_10_feeds():
    """Fixture to mock get_10_feeds service method."""
    with patch(
        "app.routes.feed_routes.get_10_feeds",
        new_callable=AsyncMock,
    ) as mock_service:
        yield mock_service


@pytest.mark.parametrize(
    "test_data,params,count",
    [
        (
            [
                {
                    "comments": [],
                    "content": "et iusto sed quo iure\nvoluptatem occaecati omnis eligendi aut ad\nvoluptatem doloribus vel accusantium quis pariatur\nmolestiae porro eius odio et labore et velit aut",
                    "id": 3,
                    "title": "ea molestias quasi exercitationem repellat qui ipsa sit aut",
                },
            ],
            "?start=0&limit=1",
            1,
        ),
        (
            [
                {
                    "userId": 1,
                    "id": 1,
                    "title": "sunt aut facere repellat provident occaecati excepturi optio reprehenderit",
                    "body": "quia et suscipit\nsuscipit recusandae consequuntur expedita et cum\nreprehenderit molestiae ut ut quas totam\nnostrum rerum est autem sunt rem eveniet architecto",
                },
                {
                    "userId": 1,
                    "id": 2,
                    "title": "qui est esse",
                    "body": "est rerum tempore vitae\nsequi sint nihil reprehenderit dolor beatae ea dolores neque\nfugiat blanditiis voluptate porro vel nihil molestiae ut reiciendis\nqui aperiam non debitis possimus qui neque nisi nulla",
                },
                {
                    "userId": 1,
                    "id": 3,
                    "title": "ea molestias quasi exercitationem repellat qui ipsa sit aut",
                    "body": "et iusto sed quo iure\nvoluptatem occaecati omnis eligendi aut ad\nvoluptatem doloribus vel accusantium quis pariatur\nmolestiae porro eius odio et labore et velit aut",
                },
                {
                    "userId": 1,
                    "id": 4,
                    "title": "eum et est occaecati",
                    "body": "ullam et saepe reiciendis voluptatem adipisci\nsit amet autem assumenda provident rerum culpa\nquis hic commodi nesciunt rem tenetur doloremque ipsam iure\nquis sunt voluptatem rerum illo velit",
                },
                {
                    "userId": 1,
                    "id": 5,
                    "title": "nesciunt quas odio",
                    "body": "repudiandae veniam quaerat sunt sed\nalias aut fugiat sit autem sed est\nvoluptatem omnis possimus esse voluptatibus quis\nest aut tenetur dolor neque",
                },
            ],
            "?start=0&limit=5",
            5,
        ),
    ],
)
def test_get_feeds_success(
    request_context,
    mock_get_10_feeds,
    captured_logs,
    test_data: List[Dict[str, Any]],
    params: str,
    count: int,
):
    async_mock = AsyncMock(return_value=test_data)
    mock_get_10_feeds.side_effect = async_mock

    with request_context(params):
        response, status_code = asyncio.run(get_feeds())

    log_counts = count_log_events(captured_logs, "get_feeds")
    test_args = mock_get_10_feeds.call_args_list[0][1]
    response_data = response.json

    mock_get_10_feeds.assert_called_once()
    assert test_args["start"] == 0
    assert test_args["limit"] == count
    assert status_code == 200
    assert response_data["success"] == True
    assert isinstance(response_data["data"], list)
    assert response_data["data"] == test_data
    assert len(response_data["data"]) == count
    assert log_counts.get("REQUEST_RECEIVED")
    assert log_counts.get("SUCCESS")
    assert not log_counts.get("ERROR")


def test_get_feeds_catch_api_exception(
    request_context, mock_get_10_feeds, captured_logs
):
    async_mock = AsyncMock(
        side_effect=APIException(
            "Connection error Unreachable", endpoint="get_feeds", method="GET"
        )
    )

    mock_get_10_feeds.side_effect = async_mock
    with request_context("?start=0&limit=10"):
        response, status_code = asyncio.run(get_feeds())

    mock_get_10_feeds.assert_called_once()
    response_data = response.json
    log_counts = count_log_events(captured_logs, "get_feeds")

    assert status_code == 502
    assert response_data["success"] == False
    assert "Connection error Unreachable" in response_data["error"]
    assert log_counts.get("REQUEST_RECEIVED")
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR") == 1


def test_get_feeds_catch_service_exception(
    request_context, mock_get_10_feeds, captured_logs
):
    """Test GET /api/feeds ServiceException case."""
    async_mock = AsyncMock(
        side_effect=ServiceException(
            "Internal Server Error", endpoint="get_feeds", method="GET"
        )
    )

    mock_get_10_feeds.side_effect = async_mock
    with request_context():
        response, status_code = asyncio.run(get_feeds())

    mock_get_10_feeds.assert_called_once()
    response_data = response.json
    log_counts = count_log_events(captured_logs, "get_feeds")

    assert status_code == 500
    assert response_data["success"] == False
    assert response_data["error"] == "Internal Server Error"
    assert log_counts.get("REQUEST_RECEIVED")
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR") == 1


@pytest.mark.parametrize(
    "params",
    [
        "?start=0&limit=k",
        "?start=a&limit=10",
        "?start=1.5&limit=10",
        "?start=0&limit=1.5",
        # "?start=-1&limit=10",
        # "?start=0&limit=-10",
    ],
)
def test_get_feeds_catch_type_and_value_error(
    request_context, mock_get_10_feeds, captured_logs, params: str
):
    with request_context(params):
        response, status_code = asyncio.run(get_feeds())

    response_data = response.json
    log_counts = count_log_events(captured_logs, "get_feeds")

    mock_get_10_feeds.assert_not_called()
    assert log_counts.get("REQUEST_RECEIVED")
    assert status_code == 400
    assert response_data["success"] == False
    assert not log_counts.get("SUCCESS")
    assert "invalid literal for int()" in response_data["error"]
    assert log_counts.get("ERROR") == 1


def test_get_feeds_catch_generic_exception(
    request_context, mock_get_10_feeds, captured_logs
):
    """Test GET /api/feeds generic Exception case."""
    async_mock = AsyncMock(side_effect=Exception("Some unexpected error occurred"))

    mock_get_10_feeds.side_effect = async_mock
    with request_context("?start=0&limit=10"):
        response, status_code = asyncio.run(get_feeds())

    mock_get_10_feeds.assert_called_once()
    response_data = response.json
    log_counts = count_log_events(captured_logs, "get_feeds")

    assert status_code == 500
    assert response_data["success"] == False
    assert "Some unexpected error" in response_data["error"]
    assert log_counts.get("REQUEST_RECEIVED")
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR") == 1
