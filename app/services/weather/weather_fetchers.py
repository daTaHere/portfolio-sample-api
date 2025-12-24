"""This module handles fetching weather data from OpenWeatherMap API asynchronously."""

# ++++++++++ Initial refactor   ++++++++++++
# - logging change for debug helper to root level
# - schmea validation external API responses, internal class and cache dto
# - unit testing
#  Implemention later

from typing import Any, Dict, List, Tuple

import httpx
import asyncio

from app.exceptions.base import APIException, ServiceException
from app.exceptions.exception_handlers import handle_route_error, handle_service_error
from app.services.cache_service import cache_set
from app.utils.route_utils import handle_route_response
from app.utils.logger_helper import handle_log, debug_logger
from app.services.weather.weather_builders import batcher

from config import Config

MAX_RETRIES = 3
HTTP_TIMEOUT_SECONDS = 5.0
RETRY_BACKOFF_BASE = 0.2  # seconds

_logger = debug_logger("weather_fetchers")


# --- Main Helper httpx request to OPENWEATHERMAP API ---
async def request_weather(lat: float, lon: float) -> Dict[str, Any]:
    """Fetch weather from OpenWeatherMap"""
    _logger.debug(
        f"Requesting weather for coords: {lat}, {lon}",
        extra={
            "module": "app/services/weather/weather_fetchers.py",
            "service_method": "request_weather ",
        },
    )
    url = f"{Config.OPENWEATHER_BASE_URL}?lat={lat}&lon={lon}&APPID={Config.OPENWEATHER_API_KEY}"
    for attempt in range(1, MAX_RETRIES + 1):
        # todo's: add retry for response error, validation error, and decoding error later
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                cache_set(f"{lat},{lon}", data, ttl=300)  # 5 min cache
                cache_set(str(data["name"]), (lat, lon), ttl=300)

                _logger.debug(
                    f" ===============   OPENWEATHER request successful for coords: {lat}, {lon}",
                    extra={
                        "module": "app/services/weather/weather_fetchers.py",
                        "service_method": "request_weather ",
                    },
                )

                return data
        except (httpx.RequestError, httpx.ConnectTimeout) as e:
            wait_time = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
            if attempt == MAX_RETRIES:
                handle_service_error(
                    e,
                    "External API Error: Unreachable",
                    "Request failed. Exhausted all retries.",
                    exc_type=APIException,
                    url=url,
                    service_method="send_request",
                )
            handle_log(
                f"Request attempt failed, retrying in {wait_time:.2f}s",
                method="GET",
                event_key="RETRIES",
                log_level="warning",
                service_method="send_request",
                endpoint=url,
                request_attempt=attempt,
                error=str(e),
            )
            await asyncio.sleep(wait_time)
        except httpx.HTTPStatusError as e:
            handle_service_error(
                e,
                f"External API Error: Bad status code: {e.response.status_code}",
                "Request returned bad status code.",
                exc_type=APIException,
                url=url,
                service_method="send_request",
            )
        # except ValidationError as e: <-- stub out for future schema validation
        #     handle_service_error(
        #         e,
        #         "External API Error: Data validation failed.",
        #         "Response data validation error.",
        #         exc_type=APIException,
        #         url=url,
        #         service_method="send_request",
        #     )
        except (TypeError, ValueError) as e:
            handle_service_error(
                e,
                "Internal Error: Type or value error.",
                "Response data type or value error.",
                event_key="ERROR",
                log_level="debug",
                exc_type=ServiceException,
                service_method="send_request",
                endpoint=url,
                error=str(e),
            )


# --- Fetch all on NO CACHE HITS ---
async def fetch_all(loc_list: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
    _logger.debug(
        f'=====  Line: 45 ======  NO CACHE HITS "fetch_all": {len(loc_list)}',
        extra={
            "module": "app/services/weather/weather_fetchers.py",
            "service_method": "fetch_all ",
        },
    )
    for batch in batcher(loc_list):
        tasks = [request_weather(lat, lon) for lat, lon in batch]
        results = await asyncio.gather(*tasks)
        return results


# --- Fetch partial on CACHE MISSES ---
async def fetch_cache_missed(
    missed_coords: List[Tuple[int, Tuple]], cached_list: List[Dict]
) -> List[Dict]:
    _logger.debug(
        f"======= Line: 60 ======  PARTIAL CACHE HIT fetch missing: {len(missed_coords)} counts",
        extra={
            "module": "app/services/weather/weather_fetchers.py",
            "service_method": "fetch_cache_missed ",
        },
    )
    response = []
    for batch in batcher(missed_coords):
        # create coroutines and request concurrently
        tasks = [fetch_with_index(idx, lat, lon) for idx, (lat, lon) in batch]
        response = await asyncio.gather(*tasks)
    # process results
    _logger.debug(
        f"======= Line: 83 ======  Attempting to process missing coordinates ========.",
        extra={
            "module": "app/services/weather/weather_fetchers.py",
            "service_method": "fetch_cache_missed ",
        },
    )
    for idx, weather_data in response:
        cached_list[idx] = weather_data
    _logger.debug(
        f"Fetch missing coords completed count: {len(cached_list)} cached",
        extra={"service_method": "fetch_cache_missed "},
    )
    return cached_list


# ---Async fetch missing coordinates ---
async def fetch_with_index(idx: int, lat: float, lon: float) -> Any:
    data = await request_weather(lat, lon)
    return idx, data
