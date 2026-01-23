"""
Comprehensive unit tests for create_model_list.
Tests for the create_model_list function in feed_builders.py.
Covers:
- Successful creation of Post and Comment model lists.
- Handling of TypeError and ValueError during model instantiation.
- Edge cases such as empty input data.
"""

import pytest

from tests.utils import count_log_events

from app.services.feeds.feed_builders import create_model_list
from app.exceptions.service import ServiceInternalException, ServiceValidationException


TEST_POST_DATA = [
    {
        "id": 1,
        "title": "Post1",
        "extra_field": "should be ignored",
    },
    {
        "id": 2,
        "title": "Post2",
        "extra_field": "should be ignored",
    },
]


@pytest.fixture
def MockModel():
    class MockModel:
        __slots__ = ["id", "title"]

        def __init__(self, data: dict):
            if data.get("fail_type") == "type":
                raise TypeError("Invalid data")
            if data.get("fail_type") == "value":
                raise ValueError("Invalid data")
            if data.get("fail_type") == "key":
                raise KeyError("Missing key")
            if data.get("fail_type") == "attribute":
                raise AttributeError("Attribute error")
            self.id = data["id"]
            self.title = data["title"]

    return MockModel


def test_create_model_list_success(captured_logs, MockModel):

    mock_data = TEST_POST_DATA

    result = create_model_list(mock_data, MockModel)

    log_counts = count_log_events(captured_logs, "create_model_list")

    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(item, MockModel) for item in result)
    assert not any(hasattr(item, "extra_field") for item in result)
    assert result[0].id == 1
    assert result[1].id == 2
    assert log_counts.get("SUCCESS")
    assert "ERROR" not in log_counts


def test_create_model_list_success_empty(captured_logs, MockModel):

    mock_data = []

    result = create_model_list(mock_data, MockModel)

    log_counts = count_log_events(captured_logs, "create_model_list")

    assert isinstance(result, list)
    assert result == []
    assert log_counts.get("SUCCESS")
    assert "ERROR" not in log_counts


def test_create_model_list_internal_error_raises_ServiceInternalException(
    captured_logs, MockModel
):
    mock_data = [
        {"id": 1, "title": "Post1", "fail_type": "attribute"},
    ]

    with pytest.raises(ServiceInternalException) as exc_info:
        create_model_list(mock_data, MockModel)

    log_counts = count_log_events(captured_logs, "create_model_list")

    assert "SUCCESS" not in log_counts
    assert log_counts.get("ERROR") == 1
    assert "Internal Error:" in str(exc_info.value)


@pytest.mark.parametrize("mock_error", ["type", "value", "key"])
def test_create_model_list_validation_error_raises_ServiceValidationException(
    captured_logs, MockModel, mock_error: str
):
    mock_data = [
        {"id": 1, "title": "Post1", "fail_type": mock_error},
    ]

    with pytest.raises(ServiceValidationException) as exc_info:
        create_model_list(mock_data, MockModel)

    log_counts = count_log_events(captured_logs, "create_model_list")

    assert "SUCCESS" not in log_counts
    assert log_counts.get("ERROR") == 1
    assert "Validation Error:" in str(exc_info.value)
