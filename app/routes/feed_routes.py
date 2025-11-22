from flask import Blueprint, jsonify
from app import logger
from app.services.feed_service import get_10_feeds


feed_bp = Blueprint("feeds", __name__)


@feed_bp.route("/feeds", methods=["GET"])
async def get_feeds():
    try:
        res = await get_10_feeds()
        return jsonify(res)
    except Exception as e:
        print(str(e))
        return jsonify({"success": False, "error": "Failed request"}, 500)
