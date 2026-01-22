"""
This module is the main weather service layer responsible
for orchestrating weather data retrieval, caching, and processing.
"""

from typing import Any, Dict, List, Tuple
from marshmallow import ValidationError

from app.exceptions.exception_handlers import handle_service_errorV2
from app.exceptions.service import ServiceInternalException, ServiceValidationException
from app.utils.logger_helper import handle_log
from app.services.weather.weather_validators import canonicalize_coords
from app.services.weather.weather_fetchers import fetch_cache_missed, fetch_all
from app.services.weather.weather_builders import (
    create_fetch_list,
    process_from_cache,
    create_weather_model,
)
from app.schemas.weather_schemas import WeatherSchema


async def get_current_weather(
    coords: Tuple[float, float] | None,
) -> List[Dict[str, Any]]:
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
            handle_log(
                "All coordinates found in cache.",
                log_level="info",
                event_key="HIT_ALL_CACHE",
                service_method="get_current_weather",
            )
            return results
        elif len(missing_coords) == len(fetch_loc):
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
            handle_log(
                "Partial cache hit, fetching missing coordinates from API.",
                log_level="info",
                event_key="PARTIAL_CACHE_MISSED",
                service_method="get_current_weather",
            )
            results = await fetch_cache_missed(missing_coords, results)
        valid_results = WeatherSchema(many=True).dump(results)
        handle_log(
            "Weather data retrieved successfully.",
            log_level="info",
            event_key="SUCCESS",
            service_method="get_current_weather",
        )
        return valid_results
    except (ValidationError, AttributeError) as e:
        handle_service_errorV2(
            e,
            "Validation Error: failed to serialize weather results via WeatherSchema.",
            exc_type=ServiceValidationException,
            service_method="get_current_weather",
            schema="WeatherSchema",
        )
    except (ValueError, TypeError, KeyError) as e:
        handle_service_errorV2(
            e,
            "Internal Error: unexpected type/value/key while processing weather results.",
            exc_type=ServiceInternalException,
            service_method="get_current_weather",
        )
