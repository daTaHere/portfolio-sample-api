from flask import Blueprint, jsonify, request
from app import logger
from app.services.feed_service import get_10_feeds
from app.exceptions.api_exceptions import APIException, ExternalAPIConnectionError


feed_bp = Blueprint("feeds", __name__)


@feed_bp.route("/feeds", methods=["GET"])
async def get_feeds():
    logger.info(
        "Incoming request",
        extra={
            "route": "/feeds",
            "method": request.method,
            "remote_ip": request.remote_addr,
        },
    )
    try:
        res = await get_10_feeds()
        logger.info(
            "Route response success",
            extra={
                "route": "/feeds",
                "status": 200,
                "items": len(res) if isinstance(res, list) else "n/a",
            },
        )
        return jsonify(res)
    except APIException as e:
        logger.error(
            "APIException occurred",
            extra={
                "route": "/feeds",
                "endpoint": e.endpoint,
                "method": e.method,
                "original_exception": str(e.original_exception),
            },
        )
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception as e:
        print(str(e))
        return jsonify({"success": False, "error": "Failed request"}, 500)
