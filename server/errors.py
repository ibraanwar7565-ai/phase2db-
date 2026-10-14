from flask import jsonify


def api_error(status, code, message):
    """The one error format used across the whole API."""
    return jsonify({
        "error": {"status": status, "code": code, "message": message}
    }), status