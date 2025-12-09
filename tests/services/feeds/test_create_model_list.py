import pytest

from unittest.mock import patch
from typing import Dict, List, Type, TypeVar
from tests.utils import count_log_events

from app.services.feeds.feed_builders import create_model_list
from app.models.post_detail_model import Post, Comment
from app.exceptions.base import ServiceException

T = TypeVar("T", bound=Post | Comment)

ERROR_TEST_DATA = [
    {
        "userId": 1,
        "id": 2,
        "title": "qui est esse",
        "body": "est rerum tempore vitae\nsequi sint nihil reprehenderit dolor beatae ea dolores neque\nfugiat blanditiis voluptate porro vel nihil molestiae ut reiciendis\nqui aperiam non debitis possimus qui neque nisi nulla",
    },
]

DEFAULT_POST_DATA = (
    [  # Post data
        {"userId": 1, "id": 2, "title": "Post1", "body": "Body1"},
        {"userId": 1, "id": 3, "title": "Post2", "body": "Body2"},
    ],
    Post,
    3,
)

DEFAULT_COMMENT_DATA = (
    [  # Comment data
        {
            "postId": 1,
            "id": 2,
            "name": "Comment1",
            "email": "a@test.com",
            "body": "Body1",
        },
        {
            "postId": 1,
            "id": 3,
            "name": "Comment2",
            "email": "b@test.com",
            "body": "Body2",
        },
    ],
    Comment,
    5,
)


@pytest.mark.parametrize(
    "input_data, model, expected_slots",
    [
        DEFAULT_POST_DATA,
        DEFAULT_COMMENT_DATA,
    ],
)
def test_create_model_list_success(
    captured_logs,
    input_data: List[Dict],
    model: Type[T],
    expected_slots: int,
):

    result = create_model_list(input_data, model)
    log_counts = count_log_events(captured_logs, "create_model_list")

    assert isinstance(result, List)
    assert (
        len(model.__slots__) == expected_slots
    )  # Verify class is not attaching unexpected attr
    assert all(
        isinstance(item, model) for item in result
    )  # Test for both Post and Comment neither has userId specifically for Post
    assert len(result) == 2
    assert result[0].id == 2
    assert result[-1].id == 3
    assert log_counts.get("CREATING_MODELS")
    assert log_counts.get("SUCCESS")
    assert not log_counts.get("ERROR")


def test_create_model_list_success_empty_response(captured_logs):
    input_data = []

    result = create_model_list(input_data, Post)
    log_counts = count_log_events(captured_logs, "create_model_list")

    assert isinstance(result, List)
    assert all(isinstance(item, Post) for item in result)
    assert len(result) == 0
    assert log_counts.get("CREATING_MODELS")
    assert log_counts.get("SUCCESS")
    assert not log_counts.get("ERROR")


@pytest.mark.parametrize(
    "test_model",
    [Post, Comment],
)
def test_create_model_list_type_error_raises_service_exception(
    captured_logs, test_model: Type[T]
):
    input_data = ERROR_TEST_DATA
    for error in [TypeError("Invalid data"), ValueError("Invalid data")]:
        with patch.object(
            test_model,
            "__init__",
            side_effect=error,
        ):
            with pytest.raises(ServiceException):
                create_model_list(input_data, test_model)

    log_counts = count_log_events(captured_logs, "create_model_list")

    assert not log_counts.get("CREATE_MODEL_LIST")
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR")
