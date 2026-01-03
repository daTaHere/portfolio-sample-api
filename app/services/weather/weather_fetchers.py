"""This module includes functions to fetch weather data from OpenWeatherMap API asynchronously."""

import asyncio
from typing import Any, Dict, List, Tuple

import httpx
from marshmallow import ValidationError

from app.exceptions.api import (
    APITimeoutException,
    APIConnectionException,
    APIBadStatusCode,
)
from app.services.cache_service import cache_set
from app.exceptions.exception_handlers import handle_api_error
from app.utils.logger_helper import handle_log
from app.services.weather.weather_builders import batcher
from app.schemas.weather_schemas import OpenWeatherSchema

from config import Config

MAX_RETRIES = 3
HTTP_TIMEOUT_SECONDS = 5.0
RETRY_BACKOFF_BASE = 0.2  # seconds


async def request_weather(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch weather data for given latitude and longitude from OpenWeatherMap API.
    Implements retries with exponential backoff for connection and timeout errors.
    """
    handle_log(
        f"Requesting weather for coords: {lat}, {lon}",
        method="GET",
        event_key="REQUEST_INITIATED",
        log_level="info",
        service_method="request_weather",
        endpoint=Config.OPENWEATHER_BASE_URL,
    )

    url = f"{Config.OPENWEATHER_BASE_URL}?lat={lat}&lon={lon}"  # Base endpoint construction
    endpoint = f"{url}&APPID={Config.OPENWEATHER_API_KEY}"  # Add API key
    validator = OpenWeatherSchema()

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            handle_log(
                f"Attempt: {attempt} for coords: {lat}, {lon}",
                method="GET",
                event_key="ATTEMPTS",
                log_level="info",
                service_method="request_weather",
                endpoint=url,
            )
            try:
                resp = await client.get(endpoint)
                resp.raise_for_status()

                data = validator.load(resp.json())

                cache_set(f"{lat},{lon}", resp.text, ttl=300)  # 5 min cache
                cache_set(str(data["name"]), (lat, lon), ttl=300)

                handle_log(
                    f"OPENWEATHER request successful for coords: {lat}, {lon}",
                    method="GET",
                    event_key="SUCCESS",
                    log_level="info",
                    service_method="request_weather",
                    endpoint=url,
                )
                return data
            except httpx.ConnectError as e:
                wait_time = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                if attempt == MAX_RETRIES:
                    handle_api_error(
                        e,
                        "Unreachable: failed to establish connection to OpenWeatherMap API.",
                        exc_type=APIConnectionException,
                        url=url,
                        method="GET",
                        service_name="OpenWeatherMap_API",
                        service_method="request_weather",
                    )
                handle_log(
                    f"CONNECT ERROR: Request attempt failed, retrying in {wait_time:.2f}s",
                    method="GET",
                    event_key="RETRIES",
                    log_level="warning",
                    service_method="request_weather",
                    endpoint=url,
                    request_attempt=attempt,
                    error=str(e),
                )
                await asyncio.sleep(wait_time)
            except (httpx.ConnectTimeout, httpx.TimeoutException) as e:
                wait_time = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                if attempt == MAX_RETRIES:
                    handle_api_error(
                        e,
                        "Unreachable: fetch failed due to timeout.",
                        exc_type=APITimeoutException,
                        url=url,
                        method="GET",
                        service_name="OpenWeatherMap_API",
                        service_method="request_weather",
                    )
                handle_log(
                    f"TIMEOUT ERROR: Request attempt failed, retrying in {wait_time:.2f}s",
                    method="GET",
                    event_key="RETRIES",
                    log_level="warning",
                    service_method="request_weather",
                    endpoint=url,
                    request_attempt=attempt,
                    error=str(e),
                )
                await asyncio.sleep(wait_time)
            except httpx.HTTPStatusError as e:
                handle_api_error(
                    e,
                    "Bad status code received from OpenWeatherMap API.",
                    exc_type=APIBadStatusCode,
                    url=url,
                    method="GET",
                    service_name="OpenWeatherMap API",
                    service_method="request_weather",
                )
            except ValidationError as e:
                handle_log(
                    "Validation Error: Invalid data format received from OpenWeatherMap API.",
                    method="GET",
                    event_key="ERROR",
                    log_level="error",
                    service_method="request_weather",
                    service_name="OpenWeatherMap_API",
                    endpoint=url,
                    error=str(e),
                )
                return {}
            except (TypeError, ValueError) as e:
                handle_log(
                    "Value/Type Error: Invalid data type received from response",
                    method="GET",
                    event_key="ERROR",
                    log_level="error",
                    service_method="request_weather",
                    service_name="OpenWeatherMap_API",
                    endpoint=url,
                    error=str(e),
                )
                return {}


async def fetch_all(loc_list: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
    """Function to fetch weather data for all coordinates in loc_list."""
    handle_log(
        "Cache miss for all coordinates, fetching all from API",
        log_level="info",
        event_key="FETCH_ALL",
        service_method="fetch_all",
        service_name="OpenWeatherMap_API",
    )
    results = []
    for batch in batcher(loc_list):
        tasks = [request_weather(lat, lon) for lat, lon in batch]
        results.extend(await asyncio.gather(*tasks))
    return results


async def fetch_cache_missed(
    missed_coords: List[Tuple[int, Tuple]], cached_list: List[Dict]
) -> List[Dict]:
    """Function to fetch weather data for partial missing coordinates in cache"""
    handle_log(
        "Fetching missing coordinates from API",
        log_level="info",
        event_key="INFO",
        service_method="fetch_cache_missed",
        service_name="OpenWeatherMap_API",
    )
    response = []
    for batch in batcher(missed_coords):
        tasks = [fetch_with_index(idx, lat, lon) for idx, (lat, lon) in batch]
        response = await asyncio.gather(*tasks)
    # process results
    for idx, weather_data in response:
        cached_list[idx] = weather_data
    handle_log(
        "Fetch missing coords completed",
        log_level="info",
        event_key="SUCCESS",
        service_method="fetch_cache_missed",
        service_name="OpenWeatherMap_API",
    )
    return cached_list


async def fetch_with_index(
    idx: int, lat: float, lon: float
) -> Tuple[int, Dict[str, Any]]:
    """Helper to fetch weather data and preserve list order"""
    handle_log(
        f"Fetch missing coord at index {idx}: {lat}, {lon}",
        method="GET",
        event_key="FETCH_WITH_INDEX",
        log_level="info",
        service_method="fetch_with_index",
    )
    data = await request_weather(lat, lon)
    return idx, data
