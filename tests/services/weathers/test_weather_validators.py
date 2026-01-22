"""
Unit tests for location and coordinate helper functions.
Covers:
- get_client_location
- geo_ip_lookup
- validate_coords_key
- truncate
- canonicalize_coords
"""

import pytest
import requests
from unittest.mock import patch, MagicMock
from typing import List

from app.services.weather.weather_validators import (
    get_client_location,
    geo_ip_lookup,
    validate_coords_key,
    truncate,
    canonicalize_coords,
)

from tests.utils import count_log_events


@pytest.fixture
def mock_requests_get():
    """Fixture to mock requests.get calls."""
    with patch("app.services.weather.weather_validators.requests.get") as mock_req:
        yield mock_req


@pytest.fixture
def patch_geo_ip_lookup(monkeypatch):
    """
    Monkeypatch geo_ip_lookup in weather_validators and provide a callable to track if it was called.
    """
    called = {"val": False}

    def mock_geo_ip():
        called["val"] = True
        return [1.1, 2.2]

    monkeypatch.setattr(
        "app.services.weather.weather_validators.geo_ip_lookup", mock_geo_ip
    )
    yield called


@pytest.mark.parametrize(
    "test_args,expected",
    [
        ({"lat": "34.05", "lon": "-118.24"}, (34.05, -118.24)),
        ({"lat": "0", "lon": "0"}, (0.0, 0.0)),
    ],
)
def test_get_client_location(monkeypatch, test_args, expected):
    class DummyRequest:
        args = test_args

    monkeypatch.setattr("app.services.weather.weather_validators.request", DummyRequest)
    result = get_client_location()

    assert result == expected
    assert isinstance(result, tuple)
    assert all(isinstance(coord, float) for coord in result)


# ------------------------------------------
#         geo_ip_lookup tests
# ------------------------------------------
def test_geo_ip_lookup_success(mock_requests_get, captured_logs):
    # Mock public IP call
    ip_mock = MagicMock()
    ip_mock.text = "1.2.3.4"
    # Mock IP info response
    info_mock = MagicMock()
    info_mock.json.return_value = {"loc": "34.05,-118.24", "lat": "34.05"}
    info_mock.raise_for_status.return_value = None

    mock_requests_get.side_effect = [ip_mock, info_mock]

    result = geo_ip_lookup()
    log_counts = count_log_events(captured_logs, "geo_ip_lookup")

    assert result == (34.05, -118.24)
    assert isinstance(result, tuple)
    assert all(isinstance(coord, float) for coord in result)
    assert log_counts.get("GEO_IP_LOOKUP") == 1
    assert not log_counts.get("IP_LOOKUP_FAILED")
    assert log_counts.get("SUCCESS") == 1
    assert not log_counts.get("ERROR")


def test_geo_ip_lookup_failure_returns_none(mock_requests_get, captured_logs):
    # Raise exception on first request
    mock_requests_get.side_effect = requests.RequestException("fail")
    result = geo_ip_lookup()

    log_counts = count_log_events(captured_logs, "geo_ip_lookup")

    assert result is None
    assert log_counts.get("GEO_IP_LOOKUP") == 1
    assert not log_counts.get("IP_LOOKUP_FAILED")
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR") == 1


#  ------------------------------------------
#            validate_coords_key tests
#  ------------------------------------------
def test_validate_coords_key_client_coords(
    monkeypatch, patch_geo_ip_lookup, captured_logs
):
    # Mock client-provided request.args
    class DummyRequest:
        args = {"lat": "34.05", "lon": "-118.24"}

    monkeypatch.setattr("app.services.weather.weather_validators.request", DummyRequest)
    result = validate_coords_key()

    log_counts = count_log_events(captured_logs, "validate_coords_key")

    assert result == (34.05, -118.24)
    assert patch_geo_ip_lookup["val"] is False
    assert log_counts.get("CLIENT_COORDS") == 1
    assert not log_counts.get("IP_GEO_LOOKUP")
    assert log_counts.get("SUCCESS") == 1


def test_validate_coords_key_fallback_to_geo_ip(
    monkeypatch, patch_geo_ip_lookup, captured_logs
):
    # No client args → use geo_ip_lookup
    class DummyRequest:
        args = {}

    monkeypatch.setattr("app.services.weather.weather_validators.request", DummyRequest)

    result = validate_coords_key()
    log_counts = count_log_events(captured_logs, "validate_coords_key")

    assert result == [1.1, 2.2]
    assert patch_geo_ip_lookup["val"] is True
    assert not log_counts.get("CLIENT_COORDS")
    assert log_counts.get("IP_GEO_LOOKUP") == 1
    assert log_counts.get("SUCCESS") == 1


# ------------------------------------------
#             truncate tests
# ------------------------------------------
@pytest.mark.parametrize(
    "value,decimals,expected",
    [
        (34.123456, 3, 34.123),
        (34.9876, 2, 34.98),
        (-118.9876, 1, -118.9),
        (0.12345, 4, 0.1234),
    ],
)
def test_truncate(value: float, decimals: int, expected: float):
    assert truncate(value, decimals) == expected


# ------------------------------------------
#           canonicalize_coords tests
# ------------------------------------------
def test_canonicalize_coords_valid(captured_logs):

    result = canonicalize_coords([34.123456, -118.9876])
    log_counts = count_log_events(captured_logs, "canonicalize_coords")
    assert result == (34.123, -118.987)

    assert log_counts.get("VALIDATE_COORDS") == 1
    assert log_counts.get("SUCCESS") == 1


@pytest.mark.parametrize(
    "bad_coords",
    [
        [200.0, -118.0],
        [34.0, -200.0],
    ],
)
def test_canonicalize_coords_invalid(bad_coords: List[float], captured_logs):

    result = canonicalize_coords(bad_coords)  # invalid latitude

    log_counts = count_log_events(captured_logs, "canonicalize_coords")

    assert result is None
    assert log_counts.get("VALIDATE_COORDS") == 1
    assert log_counts.get("ERROR") == 1
    assert not log_counts.get("SUCCESS")
