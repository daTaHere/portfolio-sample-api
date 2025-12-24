"""
This module contains the weather builders responsible for preparing
weather data for fetching and processing.
"""

# ++++++++++ Initial refactor   ++++++++++++
# - error handling
# - logging
# - schmea validation external API responses, internal class and cache dto
# - unit testing
#  Implemention later

from typing import Dict, Generator, List, Tuple

from app.exceptions.base import APIException, ServiceException
from app.exceptions.exception_handlers import handle_route_error

from app.services.cache_service import cache_get, cache_set
from app.utils.route_utils import handle_route_response
from app.utils.logger_helper import handle_log, debug_logger
from app.services.weather.weather_validators import canonicalize_coords

DEFAULT_CITIES = [
    (34.05, -118.24),  # LA
    (40.71, -74.00),  # NYC
    (41.87, -87.62),  # Chicago
    (29.76, -95.36),  # Houston
    (25.76, -80.19),  # Miami
    (51.51, -0.13),  # London
    (35.68, 139.69),  # Tokyo
    (39.90, 116.40),  # Beijing
    (30.03, 31.23),  # Cairo
    (-33.86, 151.21),  # Sydney
]

DEFAULT_BATCH_SIZE = 5

_logger = debug_logger("weather_builders")


# --- Batch generator ---
def batcher(
    lst: List[Tuple[float, float]], n: int = DEFAULT_BATCH_SIZE
) -> Generator[List[Tuple[float, float]], None, None]:
    """Yield successive n-sized chunks from list"""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def create_fetch_list(user_coords: List[float] | None) -> List[Tuple[float, float]]:
    """
    Build and order coordinates list for fetching weather data and cached list.
    returns: List of 10 tuples (lat, lon)
    - Prepends user coords if provided or part of DEFAULT_CITIES list.
    - Return DEFAULT_CITIES if user coords cannot be resolved.
    """
    _logger.debug(
        f"Create coords list for fetching weather data.",
        extra={"service_method": "create_fetch_list", "coords": user_coords},
    )
    fetch_loc = DEFAULT_CITIES.copy()
    if not user_coords:
        return fetch_loc

    if user_coords not in fetch_loc:
        _logger.debug(
            f"User coords not in default cities, prepending to fetch list.",
            extra={"service_method": "create_fetch_list", "coords": user_coords},
        )
        fetch_loc = [user_coords] + fetch_loc[:-1]  # prepend user, slice to 10
    else:
        # Swap user coords to first position
        _logger.debug(
            f"User coords found in default cities, swapping to first position.",
            extra={"service_method": "create_fetch_list", "coords": user_coords},
        )
        idx = fetch_loc.index(user_coords)
        fetch_loc[0], fetch_loc[idx] = fetch_loc[idx], fetch_loc[0]

    cache_set("weather_coords_list", fetch_loc, ttl=600)
    _logger.debug(
        f"Location list 'FINALIZED' and cached.",
        extra={
            "service_method": "create_fetch_list",
            "user_coords": user_coords,
            "fetch_count": len(fetch_loc),
        },
    )

    return fetch_loc


def process_from_cache(loc_list: List[float]) -> Tuple[List[Dict], List[Tuple]]:
    """
    Check for cache "hits" for given list of coordinates.
    return: Tuple of (cached_results_list, missing_coords_list)
    - list of cached results.
    - list of missing coords as (index, (lat, lon)) tuples.
    """
    _logger.debug(
        f"Processing cache for location list.",
        extra={"service_method": "process_from_cache", "loc_list": loc_list},
    )
    cached_results = [None] * len(loc_list)
    missing_coords: List[Tuple[int, Tuple[float, float]]] = []

    for i, (lat, lon) in enumerate(loc_list):
        cache_key = f"{lat},{lon}"
        cached = cache_get(cache_key)
        if cached:
            cached_results[i] = cached
        else:
            missing_coords.append((i, (lat, lon)))
    _logger.debug(
        f"======= Line: 100 Cache processing completed. Hits: {len(cached_results) - len(missing_coords)}, Misses: {len(missing_coords)}",
        extra={
            "service_method": "process_from_cache",
            "cache_hits": len(cached_results) - len(missing_coords),
            "cache_misses": len(missing_coords),
        },
    )
    return cached_results, missing_coords
