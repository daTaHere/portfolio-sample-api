"""
check_cache helpers unit tests.
Covers:
- Valid cache hits within range.
- Cache misses when requested range is out of bounds.
"""

import pytest
from typing import List
from app.models.feed_model import PostWithComments
from app.services.feeds.feed_validators import check_cache
from tests.utils import count_log_events

DEFAULT_MOCK_CACHE = {
    "start": 0,
    "end": 5,
    "data": [
        {
            "id": 1,
            "title": "test title 1",
        },
        {
            "id": 2,
            "title": "test title 2",
        },
        {
            "id": 3,
            "title": "test title 3",
        },
        {
            "id": 4,
            "title": "test title 4",
        },
        {
            "id": 5,
            "title": "test title 5",
        },
    ],
}


@pytest.mark.parametrize(
    "data, start, limit,response_length",
    [
        (
            DEFAULT_MOCK_CACHE,
            0,
            5,
            5,
        ),
        (
            DEFAULT_MOCK_CACHE,
            0,
            2,
            2,
        ),
        (
            DEFAULT_MOCK_CACHE,
            2,
            3,
            3,
        ),
    ],
)
def test_check_cache_success(
    captured_logs,
    data: List[PostWithComments],
    start: int,
    limit: int,
    response_length: int,
):
    result = check_cache(data, start=start, limit=limit)
    log_counts = count_log_events(captured_logs, "check_cache")

    assert isinstance(result, List)
    assert len(result) == response_length
    assert result[0]["id"] == start + 1
    assert result[-1]["id"] <= start + len(result)
    assert "CACHE_RANGE_ERROR" not in log_counts


@pytest.mark.parametrize(
    "data, start, limit",
    [
        (
            DEFAULT_MOCK_CACHE,
            0,
            8,
        ),
        (
            DEFAULT_MOCK_CACHE,
            2,
            6,
        ),
        (
            DEFAULT_MOCK_CACHE,
            6,
            2,
        ),
    ],
)
def test_check_cache_out_of_range(
    captured_logs, data: List[PostWithComments], start: int, limit: int
):
    result = check_cache(data, start=start, limit=limit)
    log_counts = count_log_events(captured_logs, "check_cache")

    assert result is None
    assert log_counts["CACHE_RANGE_ERROR"] == 1


# assert result[-1]["id"] <= start + len(result)


# @pytest.mark.parametrize(
#     "data, start, limit",
#     [
#         (
#             DEFAULT_MOCK_DATA,
#             1,
#             6,
#         ),
#         (
#             DEFAULT_MOCK_DATA,
#             0,
#             3,
#         ),
#         (
#             DEFAULT_MOCK_DATA,
#             6,
#             2,
#         ),
#     ],
# )
# def test_check_cache_out_of_range(
#     data: List[PostWithComments], start: int, limit: int, captured_logs
# ):

#     with pytest.raises(ValueError) as exc_info:
#         check_cache(data, start=start, limit=limit)
#     log_counts = count_log_events(captured_logs, "check_cache")

#     assert log_counts["CACHE_RANGE_ERROR"]
# assert "Requested range out of bounds" in str(exc_info.value)
