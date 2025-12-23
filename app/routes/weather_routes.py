"""
This module defines the weather-related route layer endpoints for the Flask application.
Routes are a fully asynchronous implementation with 3rd party API integration, caching, logging, and error handling.

"""

import httpx
import asyncio
import requests

from flask import Blueprint, request
from typing import Any, Dict, Generator, List, Tuple

from app.exceptions.base import APIException, ServiceException
from app.exceptions.exception_handlers import handle_route_error

from app.services.cache_service import cache_get, cache_set
from app.utils.route_utils import handle_route_response
from app.utils.logger_helper import handle_log, debug_logger

from config import Config

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

weather_bp = Blueprint("weather", __name__)
logger = debug_logger("weather_routes")


# --- Tructaete location data to 1 decimal to reduce cache size ---
def canonicalize_coords(lat: float, lon: float) -> Tuple[float, float]:
    """Validate, cast, truncate to 2 decimal == ~1.1km/0.7m precision"""
    lat, lon = float(lat), float(lon)
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise ValueError("Invalid coordinates")
    return (round(lat, 2), round(lon, 2))


# --- Geo IP lookup service ---
def geo_ip_look() -> float:
    """Get client IP from request and lookup geolocation"""
    client_ip = "8.8.8.8"  # For local development testing
    # For real deployment reference app/__init__.py for ProxyFix config
    # client_ip = request.remote_addr <-- Uncomment when behind trusted proxy
    ip_get = f"https://ipinfo.io/{client_ip}/json"
    ip_response = requests.get(ip_get)
    ip_data = ip_response.json()
    logger.debug(f"IP Geolocation data: {ip_data}")
    ip_lat, ip_lon = map(float, ip_data["loc"].split(","))
    return ip_lat, ip_lon


# --- async fetch weather api call ---
async def fetch_weather(lat: float, lon: float) -> Dict[str, Any]:
    """Fetch weather from OpenWeatherMap"""
    url = f"{Config.OPENWEATHER_BASE_URL}?lat={lat}&lon={lon}&APPID={Config.OPENWEATHER_API_KEY}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


# --- batching helper ---
def batches(
    lst: List[Tuple[float, float]], n: int
) -> Generator[List[Tuple[float, float]], None, None]:
    """Yield successive n-sized chunks from list"""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


# ---Async fetch missing coordinates ---
async def fetch_with_index(idx: int, lat: float, lon: float) -> Any:
    data = await fetch_weather(lat, lon)
    return idx, lat, lon, data


@weather_bp.route("/weather", methods=["GET"])
async def get_weather():
    """
    GET /weather?lat=..&lon=..
    Returns weather for requested location + default cities.
    - Attempts to use provided lat/lon query params.
    - Falls back to IP geolocation if params are missing.
    - Caches results keyed by 2 decimals lat/lon for precision.
    """
    try:
        lat = request.args.get("lat")
        lon = request.args.get("lon")

        if lat and lon:
            # Prefer user-provided coords
            user_coords = canonicalize_coords(lat, lon)
        else:
            # Fallback to geo IP lookup
            ip_lat, ip_lon = geo_ip_look()
            logger.debug(f"Geo IP coords: {type(ip_lat)}, {type(ip_lon)}")
            user_coords = canonicalize_coords(ip_lat, ip_lon)

        # ---  Prepare fetch list with ordering ---
        fetch_loc = DEFAULT_CITIES.copy()
        if user_coords not in fetch_loc:
            fetch_loc = [user_coords] + fetch_loc[:-1]  # prepend user, slice to 10
        else:
            idx = fetch_loc.index(user_coords)
            fetch_loc[0], fetch_loc[idx] = fetch_loc[idx], fetch_loc[0]

        # --- cache coords list for scheduler/polling use ---
        cache_set("weather_coords_list", fetch_loc, ttl=600)

        # --- Separate cached vs missing ---
        cached_results = [None] * len(fetch_loc)
        missing_coords: List[Tuple[int, Tuple[float, float]]] = []
        for i, (lat, lon) in enumerate(fetch_loc):
            cache_key = f"{lat},{lon}"
            cached = cache_get(cache_key)
            if cached:
                cached_results[i] = cached
            else:
                missing_coords.append((i, (lat, lon)))

        if missing_coords:
            batch_size = 5  # limit you want per batch

            for batch in batches(missing_coords, batch_size):
                # create coroutines and request concurrently
                tasks = [fetch_with_index(idx, lat, lon) for idx, (lat, lon) in batch]
                results = await asyncio.gather(*tasks)

                # process results
                for idx, lat, lon, weather_data in results:
                    cache_key = f"{lat},{lon}"
                    cache_set(cache_key, weather_data, ttl=300)  # 5 min cache
                    cache_set(str(weather_data["name"]), (lat, lon), ttl=300)
                    cached_results[idx] = weather_data
            logger.debug("======  GOTTA GET THEM ALL _______.")
        else:
            logger.debug("======    All coordinates found in cache.")

        return handle_route_response(True, cached_results, 200)

    except Exception as e:
        logger.exception("Error in /weather")
        return handle_route_response(False, str(e), 500)
