import pytest

from unittest.mock import MagicMock, patch
from typing import Generator, List

from app.services.feed_service import create_model_list
from app.models.post_detail_model import Post, Comment
from app.exceptions.base_exceptions import ServiceException

DEFAULT_INPUT_DATA = [
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


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    with patch("app.services.feed_service.logger") as mock_log:
        yield mock_log


def assert_logger_called_with(
    mock_logger: MagicMock, message_substr: str, level: str
) -> None:
    log_method = getattr(mock_logger, level)
    if not any(message_substr in str(call) for call in log_method.call_args_list):
        raise AssertionError(
            f"Expected '{message_substr}' to be logged at level '{level}'"
        )


@pytest.mark.parametrize(
    "input_data, model, expected_slots",
    [
        DEFAULT_POST_DATA,
        DEFAULT_COMMENT_DATA,
    ],
)
def test_create_model_list_success(mock_logger, input_data, model, expected_slots):

    result = create_model_list(input_data, model)
    assert_logger_called_with(mock_logger, "Model instances created", "info")

    assert isinstance(result, List)
    assert len(model.__slots__) == expected_slots
    assert all(isinstance(item, model) for item in result)
    assert len(result) == 2
    assert result[0].id == 2
    assert result[-1].id == 3
    assert all(
        not hasattr(item, "userId") for item in result
    )  # userId should not not leak into model instances


def test_create_model_list_success_empty_response(mock_logger):
    input_data = []

    result = create_model_list(input_data, Post)

    assert_logger_called_with(mock_logger, "Model instances created", "info")

    assert isinstance(result, List)
    assert all(isinstance(item, Post) for item in result)
    assert len(result) == 0


def test_create_model_list_type_error_raises_service_exception(mock_logger):
    input_data = DEFAULT_INPUT_DATA

    with patch(
        "app.services.feed_service.Post.__init__",
        side_effect=TypeError("Invalid data"),
    ):
        with pytest.raises(ServiceException):
            create_model_list(input_data, Post)

    assert_logger_called_with(mock_logger, "Error creating ", "exception")


def test_create_model_list_value_error_raises_service_exception(mock_logger):
    input_data = DEFAULT_INPUT_DATA

    with patch(
        "app.services.feed_service.Post.__init__",
        side_effect=ValueError("Invalid data"),
    ):
        with pytest.raises(ServiceException):
            create_model_list(input_data, Post)

    assert_logger_called_with(mock_logger, "Error creating ", "exception")
