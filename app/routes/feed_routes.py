from flask import Blueprint, jsonify, request
from app import logging
from app.services.feed_service import get_10_feeds
from app.exceptions.base import APIException, ServiceException

feed_bp = Blueprint("feeds", __name__)


@feed_bp.route("/feeds", methods=["GET"])
async def get_feeds():
    start = request.args.get("start", default=0, type=int)
    limit = request.args.get("limit", default=10, type=int)

    logging.info(
        "Incoming request",
        extra={
            "route": "/feeds",
            "method": request.method,
            "remote_ip": request.remote_addr,
        },
    )
    try:
        res = await get_10_feeds(start=start, limit=limit)
        logging.info(
            "Route response success",
            extra={
                "route": "/feeds",
                "status": 200,
                "items": len(res),
            },
        )
        return jsonify({"success": True, "data": res}), 200
    except APIException as e:
        # 3rd-party HTTP failure → 502
        logging.error(
            "APIException occurred",
            extra={
                "route": "/feeds",
                "endpoint": e.endpoint,
                "method": e.method,
            },
        )
        return jsonify({"success": False, "error": e.message}), 502
    except ServiceException as e:
        logging.error(
            "ServiceException occurred",
            extra={
                "route": "/feeds",
                "endpoint": e.endpoint,
                "method": e.method,
            },
        )
        return jsonify({"success": False, "error": e.message}), 500
    except Exception as e:
        logging.error(
            "Unexpected error occurred",
            extra={
                "route": "/feeds",
                "endpoint": e.endpoint,
                "method": e.method,
            },
        )
        return jsonify({"success": False, "error": e.message}), 500
