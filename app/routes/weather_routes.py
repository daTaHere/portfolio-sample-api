"""
This module defines the weather-related route layer endpoints for the Flask application.
Routes are a fully asynchronous implementation with 3rd party API integration, caching, logging, and error handling.

"""

from flask import Blueprint

from app.exceptions.api import APIConnectionException, APITimeoutException
from app.exceptions.base import APIExceptionV2, ServiceExceptionV2
from app.exceptions.exception_handlers import handle_route_error

from app.services.weather import get_current_weather
from app.services.weather.weather_validators import validate_coords_key
from app.utils.route_utils import handle_route_response
from app.utils.logger_helper import debug_logger, handle_log

weather_bp = Blueprint("weather", __name__)
_logger = debug_logger("weather_routes")


@weather_bp.route("/weather", methods=["GET"])
async def get_weather():
    """
    Weather route handler for current weather data requested from OPENWEATHER API.
    Returns weather for client location + 9 default cities.
    - Attempts to use provided lat/lon query params.
    - Falls back to IP geolocation if params are missing.
    - Returns total of 10 locations' weather data.
    """
    handle_log(
        "Received request at /weather endpoint.",
        log_level="info",
        event_key="REQUESTED",
        service_method="get_weather",
    )

    coords = validate_coords_key()
    try:
        response = await get_current_weather(coords)
        if len(response) == 0:
            handle_log(
                "No weather data found for requested locations.",
                log_level="error",
                event_key="NOT_FOUND",
                service_method="get_weather",
            )
            return handle_route_response(True, "Not Found", 404)
        return handle_route_response(True, response, 200)
    except APIConnectionException as e:
        return handle_route_response(False, str(e), 503)
    except APITimeoutException as e:
        return handle_route_response(False, str(e), 408)
    except APIExceptionV2 as e:
        handle_route_error(
            e,
            "APIException occurred",
            route="/weather",
            service_method="get_weather",
        )
        return handle_route_response(False, str(e), 502)
    except ServiceExceptionV2 as e:
        handle_route_error(
            e,
            "ServiceException occurred",
            route="/weather",
            service_method="get_weather",
        )
        return handle_route_response(False, str(e), 500)
    except (ValueError, TypeError) as e:
        handle_route_error(
            e,
            "ValueError or TypeError occurred",
            route="/weather",
            service_method="get_weather",
        )
        return handle_route_response(False, str(e), 400)
    except Exception as e:
        handle_route_error(
            e,
            "Unexpected error occurred",
            route="/weather",
            service_method="get_weather",
        )
        return handle_route_response(False, str(e), 500)
