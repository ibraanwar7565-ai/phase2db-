from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from errors import api_error
from extensions import db
from models import User
from utils import EMAIL_RE, normalize_kenyan_phone

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


def load_user():
    user_id = request.args.get("user_id", type=int)
    if not user_id or user_id <= 0:
        return None, api_error(400, "validation_error", "A valid user_id is required")
    user = db.session.get(User, user_id)
    if user is None:
        return None, api_error(404, "not_found", "User not found")
    return user, None


@users_bp.route("/profile", methods=["GET"])
def get_profile():
    user, error = load_user()
    if error:
        return error
    return jsonify({"user": user.to_dict()}), 200


@users_bp.route("/profile", methods=["PUT"])
def update_profile():
    user, error = load_user()
    if error:
        return error

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return api_error(400, "bad_request", "Provide at least one field to update")

    if "name" in data:
        name = data["name"].strip() if isinstance(data["name"], str) else ""
        if not name or len(name) > 100:
            return api_error(400, "validation_error", "name must contain 1-100 characters")
        user.name = name

    if "email" in data:
        email = data["email"].strip().lower() if isinstance(data["email"], str) else ""
        if not EMAIL_RE.fullmatch(email) or len(email) > 120:
            return api_error(400, "validation_error", "A valid email is required")
        user.email = email

    if "phone" in data:
        phone = normalize_kenyan_phone(data["phone"])
        if phone is None:
            return api_error(400, "validation_error",
                             "A valid Kenyan phone number is required, e.g. 0712345678")
        user.phone = phone

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return api_error(409, "conflict", "Email or phone number is already in use")

    return jsonify({"message": "Profile updated successfully",
                    "user": user.to_dict()}), 200