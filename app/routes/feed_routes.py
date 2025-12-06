from flask import Blueprint, jsonify, request
from typing import Any

from app.logging import logger
from app.services.feed_service import get_10_feeds
from app.exceptions.base import APIException, ServiceException
from app.exceptions.exception_handlers import handle_route_error, raise_error
from app.utils.route_utils import handle_route_response
from app.utils.logger_helper import handle_log

feed_bp = Blueprint("feeds", __name__)


@feed_bp.route("/feeds", methods=["GET"])
async def get_feeds():
    handle_log(
        "GET /feeds request received",
        method="GET",
        event_key="REQUEST_RECEIVED",
        log_level="info",
        service_method="get_feeds",
    )

    try:
        if not request.args:
            data = await get_10_feeds()
        else:
            start = int(request.args.get("start", 0))
            limit = int(request.args.get("limit", 10))
            data = await get_10_feeds(start=start, limit=limit)

    except APIException as e:
        handle_route_error(
            e,
            "APIException occurred",
            route="/feeds",
            service_method="get_feeds",
        )
        return jsonify({"success": False, "error": str(e)}), 502
    except ServiceException as e:
        handle_route_error(
            e,
            "ServiceException occurred",
            route="/feeds",
            service_method="get_feeds",
        )
        return handle_route_response(False, str(e), 500)
    except AttributeError as e:
        handle_route_error(
            e,
            "AttributeError occurred",
            route="/feeds",
            service_method="get_feeds",
        )
        return handle_route_response(False, str(e), 500)
    except (ValueError, TypeError) as e:
        handle_route_error(
            e,
            "ValueError or TypeError occurred",
            route="/feeds",
            service_method="get_feeds",
        )
        return handle_route_response(False, str(e), 400)
    except Exception as e:
        handle_route_error(
            e,
            "Unexpected error occurred",
            route="/feeds",
            service_method="get_feeds",
        )
        return handle_route_response(False, str(e), 500)

    handle_log(
        "GET /feeds request processed successfully",
        method="GET",
        event_key="SUCCESS",
        log_level="info",
        service_method="get_feeds",
        items=len(data),
    )
    return handle_route_response(True, data, 200)
