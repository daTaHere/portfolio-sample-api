import pytest
from structlog.testing import capture_logs
from unittest.mock import MagicMock, patch
from typing import Generator


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    """Patch the logger used in app.services.feed_service and yield the mock logger object."""

    with patch("app.services.feed_service.logger") as mock_logger:
        yield mock_logger


@pytest.fixture
def captured_logs():
    """
    Capture all logs emitted through structlog during a test.
    Returns a list that the test can inspect.
    """
    with capture_logs() as logs:
        yield logs
