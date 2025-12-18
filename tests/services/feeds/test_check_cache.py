import pytest
from typing import List
from app.models.feed_model import PostWithComments
from app.services.feeds.feed_validators import check_cache

DEFAULT_MOCK_DATA = {
    "start": 1,
    "end": 5,
    "data": [
        {
            "id": 1,
            "title": "test title 1",
            "body": "test body 1",
            "comments": [],
        },
        {
            "id": 2,
            "title": "test title 2",
            "body": "test body 2",
            "comments": [],
        },
        {
            "id": 3,
            "title": "test title 3",
            "body": "test body 3",
            "comments": [],
        },
        {
            "id": 4,
            "title": "test title 4",
            "body": "test body 4",
            "comments": [],
        },
        {
            "id": 5,
            "title": "test title 5",
            "body": "test body 5",
            "comments": [],
        },
    ],
}


@pytest.mark.parametrize(
    "data, start, limit",
    [
        (
            DEFAULT_MOCK_DATA,
            1,
            5,
        ),
        (
            DEFAULT_MOCK_DATA,
            2,
            3,
        ),
        (
            DEFAULT_MOCK_DATA,
            2,
            2,
        ),
    ],
)
def test_check_cache_success(data: List[PostWithComments], start: int, limit: int):
    result = check_cache(data, start=start, limit=limit)

    assert isinstance(result, List)
    assert len(result) <= limit
    assert result[0]["id"] == start
    assert result[-1]["id"] <= start + len(result)


@pytest.mark.parametrize(
    "data, start, limit",
    [
        (
            DEFAULT_MOCK_DATA,
            1,
            6,
        ),
        (
            DEFAULT_MOCK_DATA,
            0,
            3,
        ),
        (
            DEFAULT_MOCK_DATA,
            6,
            2,
        ),
    ],
)
def test_check_cache_out_of_range(data: List[PostWithComments], start: int, limit: int):

    result = check_cache(data, start=start, limit=limit)

    assert result is None
