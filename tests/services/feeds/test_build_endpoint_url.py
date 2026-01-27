import pytest

from app.services.feeds.feed_builders import build_endpoint_url
from tests.utils import count_log_events

TEST_PARAMS = [
    (
        0,
        10,
        [
            "https://jsonplaceholder.typicode.com/posts?_start=0&_limit=20",
            "https://jsonplaceholder.typicode.com/comments?_start=0&_limit=20",
        ],
    ),
    (
        5,
        20,
        [
            "https://jsonplaceholder.typicode.com/posts?_start=5&_limit=40",
            "https://jsonplaceholder.typicode.com/comments?_start=5&_limit=40",
        ],
    ),
    (
        10,
        50,
        [
            "https://jsonplaceholder.typicode.com/posts?_start=10&_limit=100",
            "https://jsonplaceholder.typicode.com/comments?_start=10&_limit=100",
        ],
    ),
    (
        # Edge case: zero limit assertion. This should never happen in practice early validation guards against it.
        0,
        0,
        [
            "https://jsonplaceholder.typicode.com/posts?_start=0&_limit=0",
            "https://jsonplaceholder.typicode.com/comments?_start=0&_limit=0",
        ],
    ),
]


@pytest.mark.parametrize("start, limit, expected", TEST_PARAMS)
def test_build_endpoint_url(captured_logs, start: int, limit: int, expected: list):

    result = build_endpoint_url(start, limit)
    log_count = count_log_events(captured_logs, "build_endpoint_url")

    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(url, str) for url in result)
    assert result == expected
    assert log_count.get("SUCCESS") == 1
