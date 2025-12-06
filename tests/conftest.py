import pytest
from app import create_app, db
from structlog.testing import capture_logs
from unittest.mock import MagicMock, patch
from typing import Any, Generator
from contextlib import contextmanager


@pytest.fixture
def app():
    """Create and configure a test application instance."""
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def request_context(app):
    """Create a test client."""

    @contextmanager
    def mock_context(params: str = "") -> Generator[Any, None, None]:
        with app.test_request_context(f"/api/feeds{params}"):
            yield

    return mock_context


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
