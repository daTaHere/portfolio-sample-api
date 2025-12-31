"""This module contains validators for weather-related data."""

# ++++++++++ Initial refactor   ++++++++++++
# - error handling
# - logging
# - schmea validation external API responses, internal class and cache dto
# - unit testing
#  Implemention later

import requests
from typing import List, Tuple

from app.exceptions.base import APIException, ServiceException
from app.exceptions.exception_handlers import handle_route_error
from app.utils.route_utils import handle_route_response
from app.utils.logger_helper import handle_log, debug_logger

_logger = debug_logger("weather_validators")


def truncate(value: float, decimals: int = 2) -> float:
    factor = 10**decimals
    return int(value * factor) / factor


# --- Tructaete location data to 1 decimal to reduce cache size ---
def canonicalize_coords(coords: List[float]) -> Tuple[float, float] | None:
    """Validate, cast, and truncate to 2 decimal == ~1.1km/0.7m precision"""
    factor = 100
    _logger.debug(
        f"====== Line: 16 ===== Canonicalizing coordinates execution. =======",
        extra={
            "module": "app/services/weather/weather_validators.py",
            "service_method": "canonicalize_coords",
            "coords": coords,
        },
    )
    lat, lon = coords
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        _logger.error(
            "==== Line: 28 ======= Lat and lon VALUE ERROR out of range.",
            extra={
                "module": "app/services/weather/weather_validators.py",
                "service_method": "canonicalize_coords",
            },
        )
        return None
    _logger.debug(
        f"======  Canonicalized coordinates: {(round(lat,2), round(lon,2))}",
        extra={
            "module": "app/services/weather/weather_validators.py",
            "service_method": "canonicalize_coords",
        },
    )
    return (truncate(lat), truncate(lon))


# --- Geo IP lookup service ---
def geo_ip_lookup() -> List[float] | None:
    """Get client IP from request and lookup geolocation"""
    _logger.debug(
        f"========== Executing geo_ip_lookup for fallback coords. =======",
        extra={
            "module": "app/services/weather/weather_validators.py",
            "service_method": "geo_ip_lookup",
        },
    )
    try:
        # Use this line in production environment (from flask import request)
        # client_ip = request.addr
        client_ip = requests.get(
            "https://api.ipify.org", timeout=2
        )  # For local testing
        ip_get = f"https://ipinfo.io/{client_ip.text.strip()}/json"
        ip_response = requests.get(ip_get, timeout=2)
        ip_response.raise_for_status()
        ip_data = ip_response.json()
        _logger.debug(f"IP Geolocation data: {ip_data}")

        if not ip_data.get("lat"):
            return None
    except Exception as e:
        # DONOT raise error!!! log and return None
        _logger.error(
            f"=========   Error fetching IP geolocation: {e}",
            extra={
                "module": "app/services/weather/weather_validators.py",
                "service_method": "geo_ip_lookup",
            },
        )
        return None
    fallback_coords = list(map(float, ip_data["loc"].split(",")))
    _logger.debug(
        f"========== Fallback ip location successful =======",
        extra={
            "module": "app/services/weather/weather_validators.py",
            "service_method": "geo_ip_lookup",
        },
    )
    return fallback_coords
