"""
This module is the main weather service layer responsible
for orchestrating weather data retrieval, caching, and processing.
"""

from typing import Any, Dict, List

from app.utils.logger_helper import handle_log, debug_logger
from app.services.weather.weather_validators import canonicalize_coords
from app.services.weather.weather_fetchers import fetch_cache_missed, fetch_all
from app.services.weather.weather_builders import (
    create_fetch_list,
    process_from_cache,
    create_weather_model,
)
from app.schemas.weather_schemas import WeatherSchema
from app.services.cache_service import cache_set
from app.dto.weather.weather_coords_cache_schema import WeatherCoordsCacheSchema

_logger = debug_logger("weather_service")


async def get_current_weather(coords: List[float] | None) -> Dict[str, Any]:
    """
    GET /weather?lat=..&lon=..
    Returns weather for requested location + default cities.
    - Attempts to use provided lat/lon query params.
    - Falls back to IP geolocation if params are missing.
    - Caches results keyed by 2 decimals lat/lon for precision.
    """
    handle_log(
        "Request for current weather data.",
        log_level="info",
        event_key="GET_WEATHER",
        service_method="get_current_weather",
    )
    user_coords = None

    try:
        if coords:
            handle_log(
                "Client provided coordinates.",
                log_level="info",
                event_key="CLIENT_COORDS",
                service_method="get_current_weather",
            )
            user_coords = canonicalize_coords(coords)

        fetch_loc = create_fetch_list(user_coords)
        results, missing_coords = process_from_cache(fetch_loc)

        if not missing_coords:
            _logger.debug(
                "===  $$$$$  CACHE HIT ON ALL $$$$$$    ===",
                extra={"service_method": "get_current_weather"},
            )
            handle_log(
                "All coordinates found in cache.",
                log_level="info",
                event_key="HIT_ALL_CACHE",
                service_method="get_current_weather",
            )
            return results
        elif len(missing_coords) == len(fetch_loc):
            _logger.debug(
                "===  ?????  ???? MISSED ON ALL on cache. ??????    ===",
                extra={"service_method": "get_current_weather"},
            )
            handle_log(
                "Cache missed all coordinates, fetching all from API.",
                log_level="info",
                event_key="MISSED_ALL_CACHE",
                service_method="get_current_weather",
            )
            resp = await fetch_all(fetch_loc)
            current_data = create_weather_model(resp)

            results = current_data
        else:
            _logger.debug(
                "*****   PARTIAL CACHE MISS, FETCHING MISSING FROM API  ++++++++",
                extra={"service_method": "get_current_weather"},
            )
            handle_log(
                "Partial cache hit, fetching missing coordinates from API.",
                log_level="info",
                event_key="PARTIAL_CACHE_MISSED",
                service_method="get_current_weather",
            )

            results = await fetch_cache_missed(missing_coords, results)

        _logger.debug(
            "===   WEATHER DATA RETRIEVED SUCCESSFULLY         ===          ",
            extra={"service_method": "get_current_weather"},
        )
        handle_log(
            "Weather data retrieved successfully.",
            log_level="info",
            event_key="SUCCESS",
            service_method="get_current_weather",
        )
        return WeatherSchema(many=True).dump(results)
    except (ValueError, TypeError) as e:
        _logger.exception(
            "Error in /weather", extra={"service_method": "get_current_weather"}
        )
