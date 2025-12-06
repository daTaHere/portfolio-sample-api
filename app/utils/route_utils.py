from typing import Any
from flask import jsonify


def handle_route_response(success: bool, response: Any, code: int):
    if success:
        return jsonify({"success": True, "data": response}), code
    else:
        return jsonify({"success": False, "error": response}), code
