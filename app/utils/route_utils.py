from flask import jsonify
from typing import Any


def handle_route_response(success: bool, response: Any, code: int):
    """Formats and returns a standardized JSON response for Flask routes."""

    if success:
        return jsonify({"success": True, "data": response}), code
    else:
        return jsonify({"success": False, "error": response}), code
