"""
This module contains the weather builders responsible for preparing
weather data for fetching and processing.
"""

from typing import Any, Dict, Generator, List, Tuple
from marshmallow import ValidationError

from app.dto.weather.weather_coords_cache_schema import WeatherCoordsCacheSchema
from app.exceptions.exception_handlers import handle_service_errorV2
from app.exceptions.service import (
    ServiceInternalException,
    ServiceValidationException,
)
from app.models.weather_model import WeatherModel
from app.services.cache_service import cache_get, cache_set
from app.schemas.weather_schemas import WeatherSchema
from app.utils.logger_helper import handle_log


DEFAULT_CITIES = [
    (34.050, -118.240),  # LA
    (40.710, -74.000),  # NYC
    (41.870, -87.620),  # Chicago
    (29.760, -95.360),  # Houston
    (25.760, -80.190),  # Miami
    (51.510, -0.130),  # London
    (35.680, 139.690),  # Tokyo
    (39.900, 116.400),  # Beijing
    (30.030, 31.230),  # Cairo
    (-33.860, 151.210),  # Sydney
]

DEFAULT_BATCH_SIZE = 5


def batcher(
    lst: List[Tuple[float, float]], n: int = DEFAULT_BATCH_SIZE
) -> Generator[List[Tuple[float, float]], None, None]:
    """Helper to batch a list into chunks of size n"""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def create_fetch_list(
    user_coords: Tuple[float, float] | None,
) -> List[Tuple[float, float]]:
    """
    Build and order coordinates list for fetching weather.
    returns: List of 10 tuples (lat, lon)
    - Prepends user coords if provided or part of DEFAULT_CITIES list.
    - Return DEFAULT_CITIES if user coords cannot be resolved.
    """
    handle_log(
        "Build coords list for fetching weather data.",
        log_level="info",
        event_key="INFO",
        service_method="create_fetch_list",
    )

    fetch_loc = DEFAULT_CITIES.copy()
    if not user_coords:
        handle_log(
            "No user coordinates provided, fallback to default cities.",
            log_level="info",
            event_key="GET_DEFAULT_CITIES",
            service_method="create_fetch_list",
        )
        return fetch_loc

    if user_coords not in fetch_loc:
        handle_log(
            "User location not a default city, prepending to list.",
            log_level="info",
            event_key="PREPEND_USER_COORDS",
            service_method="create_fetch_list",
            coords=user_coords,
        )
        fetch_loc = [user_coords] + fetch_loc[:-1]  # prepend user, slice to 10
    else:
        handle_log(
            "User location is a default city, swapping to first position.",
            log_level="info",
            event_key="SWAP_LOCATION_ORDER",
            service_method="create_fetch_list",
        )
        idx = fetch_loc.index(user_coords)
        fetch_loc[0], fetch_loc[idx] = fetch_loc[idx], fetch_loc[0]

    handle_log(
        "Location list 'FINALIZED' and cached.",
        log_level="info",
        event_key="SUCCESS",
        service_method="create_fetch_list",
    )

    return fetch_loc


def process_from_cache(
    loc_list: List[Tuple[float, float]],
) -> Tuple[List[Dict], List[Tuple[float, float]]]:
    """
    Process location list against cache, returning cached results and missing coords.
    Args:
        loc_list: List of tuples (lat, lon)
    Returns:
        cached_results: List of cached weather data dicts or Nones
        missing_coords: List of tuples (index, (lat, lon)) for cache misses
    """

    handle_log(
        "Processing cache for location list.",
        log_level="info",
        event_key="PROCESS_FROM_CACHE",
        service_method="process_from_cache",
    )

    # Initialize results list and empty list for missing coordinates
    cached_results = [None] * len(loc_list)
    missing_coords: List[Tuple[int, Tuple[float, float]]] = []

    # Check cache for each coordinate and deserialize and populate result List if "hit" or append to misses List
    for i, (lat, lon) in enumerate(loc_list):
        cache_key = f"{lat},{lon}"
        cached = cache_get(cache_key)
        if not cached:
            missing_coords.append((i, (lat, lon)))
            continue
        try:
            cached_results[i] = WeatherSchema().load(cached)
        except (ValidationError, TypeError, ValueError) as e:
            handle_log(
                "Cache deserialization error.",
                log_level="warning",
                event_key="CACHE_DESERIALIZATION_ERROR",
                service_method="process_from_cache",
                coords=(lat, lon),
                error=str(e),
            )
            missing_coords.append((i, (lat, lon)))

    handle_log(
        "Cache processing complete.",
        log_level="info",
        event_key="SUCCESS",
        service_method="process_from_cache",
        missing_count=len(missing_coords),
        cached_count=len(loc_list) - len(missing_coords),
    )
    if len(missing_coords) > 0:
        cache_set(
            "weather_coords_list",
            WeatherCoordsCacheSchema().dump({"coords": loc_list}),
            ttl=200,
        )
        handle_log(
            "Updated cached weather coordinates list.",
            log_level="info",
            event_key="WEATHER_COORDS_CACHED",
            service_method="process_from_cache",
        )

    return cached_results, missing_coords


def create_weather_model(weather_data: List[Dict[str, Any]]) -> List[WeatherModel]:
    """Validate and create WeatherModel instances from raw weather data list."""
    handle_log(
        "Creating WeatherModel instances from weather data.",
        log_level="info",
        event_key="INFO",
        service_method="create_weather_model",
    )
    weather_models = []
    try:
        for item in weather_data:
            weather_instance = WeatherModel(item)
            lat, lon = weather_instance.coord.values()
            valid_data = WeatherSchema().dump(weather_instance)
            cache_set(
                f"{lat},{lon}",
                valid_data,
                ttl=200,
            )
            weather_models.append(weather_instance)
        handle_log(
            "WeatherModel instances created successfully.",
            log_level="info",
            event_key="SUCCESS",
            service_method="create_weather_model",
            count=len(weather_models),
        )
        return weather_models
    except (ValueError, TypeError, AttributeError) as e:
        handle_service_errorV2(
            e,
            "Internal Error: processing weather data into WeatherModel instances.",
            exc_type=ServiceInternalException,
            service_method="create_weather_model",
            model="WeatherModel",
        )
    except ValidationError as e:
        handle_service_errorV2(
            e,
            "Validation Error: while serializing weather data.",
            exc_type=ServiceValidationException,
            service_method="create_weather_model",
            schema="WeatherSchema",
        )
