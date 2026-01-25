"""normalize_pagination test unit covers valid and invalid inputs."""

from typing import Tuple
import pytest
from tests.utils import count_log_events
from app.services.feeds.feed_validators import normalize_pagination


TEST_VALID_PARAMS = [
    (0, 10),
    (5, 20),
    (10, 100),
]

TEST_INVALID_PARAMS = [
    (-1, 10),
    (0, 0),
    (5, -5),
    (10, 150),
]


@pytest.mark.parametrize("mock_params", TEST_VALID_PARAMS)
def test_normalize_pagination_success(captured_logs, mock_params: Tuple[int, int]):

    result = normalize_pagination(mock_params)
    log_count = count_log_events(captured_logs, "normalize_pagination")

    assert isinstance(result, tuple)
    assert len(result) == 2
    assert all(isinstance(i, int) for i in result)
    assert result == mock_params
    assert "INVALID__ERROR" not in log_count


@pytest.mark.parametrize("mock_params", TEST_INVALID_PARAMS)
def test_normalize_pagination_failure(captured_logs, mock_params: Tuple[int, int]):

    result = normalize_pagination(mock_params)
    log_count = count_log_events(captured_logs, "normalize_pagination")

    assert result is None
    assert log_count.get("INVALID__ERROR") == 1
