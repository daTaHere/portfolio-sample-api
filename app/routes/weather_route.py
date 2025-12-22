"""
This module defines the weather-related route layer endpoints for the Flask application.
Routes are a fully asynchronous implementation with 3rd party API integration, caching, logging, and error handling.

"""

import httpx
import asyncio
from flask import Blueprint, request

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


# -- coordinate validation helper ---
def canonicalize_coords(lat, lon):
    """Validate, cast, truncate to 2 decimals"""
    lat, lon = float(lat), float(lon)
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise ValueError("Invalid coordinates")
    return (round(lat, 2), round(lon, 2))


# --- async fetch weather api call ---
async def fetch_weather(lat, lon):
    """Fetch weather from OpenWeatherMap"""
    url = f"{Config.OPENWEATHER_BASE_URL}?lat={lat}&lon={lon}&APPID={Config.OPENWEATHER_API_KEY}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


#  --- geo IP lookup stubbed out for future implementation ---
def geo_ip_look(lat, lon):
    """Validate, cast, truncate to 2 decimals"""
    lat, lon = float(lat), float(lon)
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise ValueError("Invalid coordinates")
    return round(lat, 2), round(lon, 2)


# --- batching helper ---
def batches(lst, n):
    """Yield successive n-sized chunks from list"""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


# ---Async fetch missing coordinates ---
async def fetch_with_index(idx, lat, lon):
    data = await fetch_weather(lat, lon)
    return idx, lat, lon, data


@weather_bp.route("/weather", methods=["GET"])
async def get_weather():
    """
    GET /weather?lat=..&lon=..
    Returns weather for requested location + default cities
    """

    try:
        # --- 1️⃣ Resolve user location ---
        lat = request.args.get("lat")
        lon = request.args.get("lon")
        if lat and lon:
            user_coords = canonicalize_coords(lat, lon)
        else:
            pass

        # --- 2️⃣ Prepare fetch list with ordering ---
        fetch_loc = DEFAULT_CITIES.copy()
        if user_coords not in fetch_loc:
            fetch_loc = [user_coords] + fetch_loc[:-1]  # prepend user, slice to 10
        else:
            idx = fetch_loc.index(user_coords)
            fetch_loc[0], fetch_loc[idx] = fetch_loc[idx], fetch_loc[0]

        # --- 3️⃣ Separate cached vs missing ---
        cached_results = [None] * len(fetch_loc)
        missing_coords = []
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
                # create coroutines for this batch
                tasks = [fetch_with_index(idx, lat, lon) for idx, (lat, lon) in batch]
                # run them concurrently
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
