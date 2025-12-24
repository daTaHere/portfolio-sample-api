"""
This module defines the weather-related route layer endpoints for the Flask application.
Routes are a fully asynchronous implementation with 3rd party API integration, caching, logging, and error handling.

"""

from flask import Blueprint, request

from app.exceptions.base import APIException, ServiceException
from app.exceptions.exception_handlers import handle_route_error

from app.services.weather import get_current_weather

from app.utils.route_utils import handle_route_response
from app.utils.logger_helper import debug_logger

from app.services.weather.weather_validators import geo_ip_lookup


weather_bp = Blueprint("weather", __name__)
_logger = debug_logger("weather_routes")


@weather_bp.route("/weather", methods=["GET"])
async def get_weather():
    """
    GET /weather?lat=..&lon=..
    Returns weather for requested location + default cities.
    - Attempts to use provided lat/lon query params.
    - Falls back to IP geolocation if params are missing.
    - Caches results keyed by 2 decimals lat/lon for precision.
    """
    _logger.debug(
        "==============  Received request at /weather endpoint.  ========================="
    )
    if request.args:
        lat = request.args.get("lat")
        lon = request.args.get("lon")
        coords = list(map(float, [lat, lon]))
        _logger.debug(
            f"========= lat/lon provided by geodecoder : {coords} ============= "
        )
    else:
        coords = geo_ip_lookup()
        _logger.debug(f"========= lat/lon from IP lookup: {coords} ============= ")

    try:
        response = await get_current_weather(coords)
        _logger.debug(
            f"Weather route response: 200 OK ======= response count: {len(response)} "
        )
        return handle_route_response(True, response, 200)

    except Exception as e:
        _logger.exception("Error in /weather")
        return handle_route_response(False, str(e), 500)
