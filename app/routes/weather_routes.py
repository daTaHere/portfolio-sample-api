"""
This module defines the weather-related route layer endpoints for the Flask application.
Routes are a fully asynchronous implementation with 3rd party API integration, caching, logging, and error handling.

"""

from flask import Blueprint, request
from typing import Any, Dict, List, Tuple

from app.exceptions.base import APIException, ServiceException
from app.exceptions.exception_handlers import handle_route_error
from app.exceptions.api import APIConnectionException, APITimeoutException

from app.services.weather import get_current_weather

from app.utils.route_utils import handle_route_response
from app.utils.logger_helper import debug_logger, handle_log

from app.services.weather.weather_validators import get_client_location, geo_ip_lookup


weather_bp = Blueprint("weather", __name__)
_logger = debug_logger("weather_routes")


@weather_bp.route("/weather", methods=["GET"])
async def get_weather():
    """
    Weather route handler for current weather data requsted from OPENWEATHER API.
    Returns weather for client location + 9 default cities.
    - Attempts to use provided lat/lon query params.
    - Falls back to IP geolocation if params are missing.
    - Returns total of 10 locations' weather data.
    """
    handle_log(
        "Received request at /weather endpoint.",
        log_level="info",
        event_key="REQUESTED",
        service_method="get_weather ",
    )
    if request.args:
        handle_log(
            "Client provided current location coordinates.",
            log_level="info",
            event_key="CLIENT_COORDS",
            service_method="get_weather ",
        )
        coords = get_client_location()
    else:
        handle_log(
            "Attempting to geolocate by IP.",
            log_level="info",
            event_key="IP_GEOLOOKUP",
            service_method="get_weather ",
        )
        coords = geo_ip_lookup()

    try:
        response = await get_current_weather(coords)
        if len(response) == 0:
            handle_log(
                "No weather data found for requested locations.",
                log_level="error",
                event_key="NOT_FOUND",
                service_method="get_weather ",
            )
            return handle_route_response(True, "Not Found", 404)
        return handle_route_response(True, response, 200)
    except APIConnectionException as e:
        return handle_route_response(False, str(e), 503)
    except APITimeoutException as e:
        return handle_route_response(False, str(e), 408)
