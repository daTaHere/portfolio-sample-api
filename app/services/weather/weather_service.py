"""
This module is the main weather service layer responsible
for orchestrating weather data retrieval, caching, and processing.
"""

# ++++++++++ Initial refactor   ++++++++++++
# - error handling
# - logging
# - schmea validation external API responses, internal class and cache dto
# - unit testing
#  Implemention later


from typing import Any, Dict, List

from app.exceptions.base import APIException, ServiceException
from app.exceptions.exception_handlers import handle_route_error

from app.utils.route_utils import handle_route_response
from app.utils.logger_helper import handle_log, debug_logger
from app.services.weather.weather_validators import canonicalize_coords
from app.services.weather.weather_fetchers import fetch_cache_missed, fetch_all
from app.services.weather.weather_builders import create_fetch_list, process_from_cache

_logger = debug_logger("weather_service")


async def get_current_weather(coords: List[float] | None) -> Dict[str, Any]:
    """
    GET /weather?lat=..&lon=..
    Returns weather for requested location + default cities.
    - Attempts to use provided lat/lon query params.
    - Falls back to IP geolocation if params are missing.
    - Caches results keyed by 2 decimals lat/lon for precision.
    """
    _logger.debug(
        "==============  get_current_weather service called.  =========================",
        extra={
            "module": "app/services/weather/weather_service.py",
            "service_method": "get_current_weather",
        },
    )
    user_coords = None

    try:
        if coords:
            _logger.debug(
                "====== Line: 45  Canonicalizing provided coordinates. ========",
                extra={
                    "module": "app/services/weather/weather_service.py",
                    "service_method": "get_current_weather",
                },
            )
            user_coords = canonicalize_coords(coords)
        _logger.debug(
            "====== Line: 54  Creating fetch location list. ========",
            extra={
                "module": "app/services/weather/weather_service.py",
                "service_method": "get_current_weather",
            },
        )
        fetch_loc = create_fetch_list(user_coords)

        _logger.debug(
            "====== Line: 54  Processing cache for fetch location list. ========",
            extra={
                "module": "app/services/weather/weather_service.py",
                "service_method": "get_current_weather",
            },
        )
        results, missing_coords = process_from_cache(fetch_loc)

        if missing_coords:
            _logger.debug(
                f"====== Line: 47  Missing coordinates from cache. ========",
                extra={
                    "module": "app/services/weather/weather_service.py",
                    "service_method": "get_current_weather",
                },
            )
            if len(missing_coords) == len(fetch_loc):
                _logger.debug(
                    "====== Line: 50  GOTTA GET THEM ALL.",
                    extra={
                        "module": "app/services/weather/weather_service.py",
                        "service_method": "get_current_weather",
                    },
                )
                _logger.debug(
                    f"====== Line: 52 FULL Fetch ALL ---> {fetch_loc} ========"
                )
                return await fetch_all(fetch_loc)

            results = await fetch_cache_missed(missing_coords, results)
            _logger.debug(
                "====== Line: 56  Partial CACHE HIT - fetched missing coords. ========",
                extra={
                    "module": "app/services/weather/weather_service.py",
                    "service_method": "get_current_weather",
                },
            )

        _logger.debug(
            f"====== Line: 62  Weather data retrieval complete. ========",
            extra={
                "module": "app/services/weather/weather_service.py",
                "service_method": "get_current_weather",
            },
        )
        return results

    except (ValueError, TypeError) as e:
        _logger.exception(
            "Error in /weather", extra={"service_method": "get_current_weather"}
        )
