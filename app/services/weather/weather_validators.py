"""This module contains validators for weather-related data."""

import requests
from flask import request
from typing import List, Tuple

from app.utils.logger_helper import handle_log, debug_logger

_logger = debug_logger("weather_validators")


def get_client_location() -> Tuple[float, float]:
    """Extract client-provided lat/lon from query parameters."""
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    return tuple(map(float, [lat, lon]))


# --- Geo IP lookup service ---
def geo_ip_lookup() -> Tuple[float, float] | None:
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
        fallback_coords = tuple(map(float, ip_data["loc"].split(",")))
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


def validate_coords_key() -> Tuple[float, float] | None:
    """Return pair of coordinates else None."""

    if request.args.get("lat") and request.args.get("lon"):
        _logger.debug(
            "===  $$$$$  CLIENT PROVIDED COORDS  $$$$$$    ===",
            extra={"service_method": "get_weather "},
        )
        handle_log(
            "Client provided current location coordinates.",
            log_level="info",
            event_key="CLIENT_COORDS",
            service_method="validate_coords_key",
        )

        coords = get_client_location()
    else:
        handle_log(
            "Attempting to geolocate by IP.",
            log_level="info",
            event_key="IP_GEO_LOOKUP",
            service_method="validate_coords_key",
        )
        _logger.debug(
            "===  $$$$$  GEO IP LOOKUP FOR COORDS  $$$$$$    ===",
            extra={"service_method": "get_weather "},
        )
        coords = geo_ip_lookup()

    handle_log(
        "Coordinates validation complete.",
        log_level="info",
        event_key="SUCCESS",
        service_method="validate_coords_key",
    )

    return coords


def truncate(value: float, decimals: int = 3) -> float:
    """Format coordinates to fixed decimal. Default precision is 3 decimals."""
    factor = 10**decimals
    return int(value * factor) / factor


# --- Truncate location data to 3 decimals to ensure city level accuracy ---
def canonicalize_coords(coords: Tuple[float, float]) -> Tuple[float, float] | None:
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
