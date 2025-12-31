"""
Comprehensive unit tests for the request_weather function.
Covers:
- Successful data retrieval.
- Handling transport layer errors with retries.
- Correct exception raising for various failure scenarios.
- Asynchronous HTTP request mocking with respx.
"""

from unittest.mock import patch
from typing import Any, List

import pytest
import respx
import httpx

from app.services.weather.weather_fetchers import (
    fetch_all,
    fetch_cache_missed,
    fetch_with_index,
)
from app.exceptions.api import (
    APIBadStatusCode,
    APIConnectionException,
    APITimeoutException,
)
from tests.utils import count_log_events
