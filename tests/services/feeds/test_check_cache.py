import pytest
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch
from app.services.feeds.feed_validators import check_cache


@pytest.fixture
def mock_cache_get() -> Generator[MagicMock, None, None]:
    with patch("app.services.feeds.feed_validators.cache_get") as mock:
        yield mock  # yields the active mock


@pytest.mark.parametrize(
    "start, limit, data, expected_result",
    [
        (
            0,
            2,
            {
                "start": 0,
                "end": 2,
                "data": [0, 1, 2],
            },
            [0, 1],
        ),
        (
            1,
            2,
            {
                "start": 0,
                "end": 2,
                "data": [0, 1, 2],
            },
            [1, 2],
        ),
        (
            0,
            2,
            None,
            None,
        ),
        (
            3,
            2,
            {
                "start": 0,
                "end": 2,
                "data": [0, 1, 2],
            },
            None,
        ),
    ],
)
def test_check_cache_success(
    mock_cache_get, start: int, limit: int, data: Dict[str, Any], expected_result
):
    mock_cache_get.return_value = data
    result = check_cache("feeds", start=start, limit=limit)

    assert result == expected_result
