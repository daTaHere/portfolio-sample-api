"""This module contains all weather feature related route controllers."""

from flask import Blueprint

from app.exceptions.api import (
    APITimeoutException,
    APIConnectionException,
    APIJSONDecodeException,
    APIBadStatusCode,
)
from app.exceptions.service import ServiceInternalException, ServiceValidationException

from app.services.weather import get_current_weather
from app.services.weather.weather_validators import validate_coords_key
from app.utils.route_utils import handle_route_response
from app.utils.logger_helper import handle_log

weather_bp = Blueprint("weather", __name__)


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
        "Inbound weather request received.",
        method="GET",
        log_level="info",
        event_key="REQUESTED",
        service_method="get_weather",
        route="/weather",
    )

    try:
        coords = validate_coords_key()
        weather_data = await get_current_weather(coords)
        if not weather_data:
            handle_log(
                "Weather service returned no results.",
                method="GET",
                log_level="warning",
                event_key="NOT_FOUND",
                service_method="get_weather",
                route="/weather",
            )
            return handle_route_response(True, "Not Found", 404)

        handle_log(
            "Weather data successfully retrieved.",
            method="GET",
            log_level="info",
            event_key="SUCCESS",
            service_method="get_weather",
            route="/weather",
        )

        return handle_route_response(True, weather_data, 200)

    except ServiceValidationException as exc:
        handle_log(
            "Invalid input provided to weather service.",
            log_level="error",
            event_key="VALIDATION_ERROR",
            route="/weather",
            service_method="get_weather",
        )
        return handle_route_response(False, str(exc), 400)

    except (APITimeoutException, TimeoutError) as exc:
        handle_log(
            "Unreachable: client request timed out",
            log_level="error",
            event_key="TIMEOUT_ERROR",
            route="/weather",
            service_method="get_weather",
        )
        return handle_route_response(False, str(exc), 408)

    except APIBadStatusCode as exc:
        handle_log(
            "Service returned bad status code",
            log_level="error",
            event_key="BAD_STATUS_CODE",
            route="/weather",
            service_method="get_weather",
        )
        return handle_route_response(False, str(exc), 502)

    except APIConnectionException as e:
        handle_log(
            "Unreachable: client connection error",
            log_level="error",
            event_key="CONNECTION_ERROR",
            route="/weather",
            service_method="get_weather",
        )
        return handle_route_response(False, str(e), 503)

    except (
        APIJSONDecodeException,
        ServiceInternalException,
        ValueError,
        TypeError,
    ) as e:
        handle_log(
            "Service returned bad response",
            log_level="error",
            event_key="RESPONSE_ERROR",
            route="/weather",
            service_method="get_weather",
        )
        return handle_route_response(False, str(e), 500)

    except Exception as e:
        handle_log(
            "Unexpected error occurred",
            log_level="error",
            event_key="ERROR",
            route="/weather",
            service_method="get_weather",
        )
        return handle_route_response(False, str(e), 500)
