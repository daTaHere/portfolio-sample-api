"""
This module defines the feed-related routes layer endpoints for the Flask application.
Routes are fully asynchronous implementation with 3rd party API integration, caching, logging, and error handling.

"""

from flask import Blueprint, request

from app.services.feeds.feed_service import get_10_feeds
from app.schemas.feed_schemas import PostWithCommentsSchema

from app.exceptions.base import APIException, ServiceException
from app.exceptions.exception_handlers import handle_route_error

from app.utils.route_utils import handle_route_response
from app.utils.logger_helper import handle_log


feed_bp = Blueprint("feeds", __name__)


@feed_bp.route("/feeds", methods=["GET"])
async def get_feeds():
    """
    This GET endpoint retrieves a list of feed posts with their associated comments.
    Query Parameters (optional):
        - start (int): The starting index for pagination. (default is 0)
        - limit (int): The number of posts to retrieve. (default is 10)
    Returns:
        JSON: Array of feed posts with comments and 200 status
    """
    handle_log(
        "GET /feeds request received",
        method="GET",
        event_key="REQUEST_RECEIVED",
        log_level="info",
        service_method="get_feeds",
    )

    try:
        if not request.args:
            # No query parameters, use defaults
            res = await get_10_feeds()
        else:
            start = int(request.args.get("start"))
            limit = int(request.args.get("limit"))
            res = await get_10_feeds(start=start, limit=limit)
        data = PostWithCommentsSchema(many=True).dump(res)
    except APIException as e:
        handle_route_error(
            e,
            "APIException occurred",
            route="/feeds",
            service_method="get_feeds",
        )
        return handle_route_response(False, str(e), 502)
    except ServiceException as e:
        handle_route_error(
            e,
            "ServiceException occurred",
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
