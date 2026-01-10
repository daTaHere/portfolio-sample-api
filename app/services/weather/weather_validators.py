"""This module contains validators for weather-related data."""

# ++++++++++ Initial refactor   ++++++++++++
# - error handling
# - logging
# - schmea validation external API responses, internal class and cache dto
# - unit testing
#  Implemention later

import requests
from flask import request
from typing import Any, Dict, List, Tuple

from app.exceptions.base import APIException, ServiceException
from app.exceptions.exception_handlers import handle_route_error
from app.utils.route_utils import handle_route_response
from app.utils.logger_helper import handle_log, debug_logger


_logger = debug_logger("weather_validators")


def truncate(value: float, decimals: int = 3) -> float:
    """Format cordinates to fixed decimal. Default prescision is 3 decimals."""
    factor = 10**decimals
    return int(value * factor) / factor


def get_client_location() -> list[float]:
    """Extract client-provided lat/lon from query parameters."""
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    return list(map(float, [lat, lon]))


# --- Tructaete location data to 1 decimal to reduce cache size ---
def canonicalize_coords(coords: List[float]) -> Tuple[float, float] | None:
    """Validate range and format coordinates to 3 decimal places."""
    handle_log(
        "Canonicalizing coordinates for cache key.",
        log_level="info",
        event_key="VALIDATE_COORDS",
        service_method="canonicalize_coords",
    )
    lat, lon = coords
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        handle_log(
            "Coordinates out of valid range.",
            log_level="error",
            event_key="ERROR",
            service_method="canonicalize_coords",
            lat=lat,
            lon=lon,
        )
        return None
    handle_log(
        "Coordinates validated and canonicalized.",
        log_level="info",
        event_key="SUCCESS",
        service_method="canonicalize_coords",
    )

    return (truncate(lat), truncate(lon))


# --- Geo IP lookup service ---
def geo_ip_lookup() -> List[float] | None:
    """Fallback to IP geolocation to get lat/lon if client does not provide."""
    handle_log(
        "Performing IP geolocation lookup.",
        log_level="info",
        event_key="GEO_IP_LOOKUP",
        service_method="geo_ip_lookup",
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

        if not ip_data.get("lat"):
            handle_log(
                "Failed to resolve geolocation from IP data.",
                log_level="info",
                event_key="IP_LOOKUP_FAILED",
                service_method="geo_ip_lookup",
            )
            return None
        fallback_coords = list(map(float, ip_data["loc"].split(",")))
        handle_log(
            "IP geolocation lookup successful.",
            log_level="info",
            event_key="SUCCESS",
            service_method="geo_ip_lookup",
        )
        return fallback_coords
    except Exception as e:
        # DO NOT raise error!!! log and return None
        handle_log(
            f"Exception during IP geolocation lookup: {str(e)}",
            log_level="error",
            event_key="ERROR",
            service_method="geo_ip_lookup",
        )
        return None
