from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from errors import api_error
from extensions import db
from models import User
from utils import EMAIL_RE, normalize_kenyan_phone

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _phone_is_registered(normalized_phone):
    return any(
        normalize_kenyan_phone(phone) == normalized_phone
        for (phone,) in db.session.query(User.phone).all()
        if phone
    )


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}

    name_value = data.get("name")
    if not isinstance(name_value, str) or not name_value.strip() or len(name_value.strip()) > 100:
        return api_error(400, "invalid_name", "Enter your full name.")
    name = name_value.strip()

    email_value = data.get("email")
    if not isinstance(email_value, str):
        return api_error(400, "invalid_email", "Enter a valid email address.")
    email = email_value.strip().lower()
    if len(email) > 120 or not EMAIL_RE.fullmatch(email):
        return api_error(400, "invalid_email", "Enter a valid email address.")

    phone_value = data.get("phone")
    phone = normalize_kenyan_phone(phone_value)
    if phone is None:
        return api_error(
            400,
            "invalid_phone",
            "Enter a valid Kenyan phone number, for example 0712 345 678.",
        )

    password = data.get("password")
    if not isinstance(password, str) or not 8 <= len(password) <= 128:
        return api_error(400, "weak_password", "Password must be 8 to 128 characters.")

    if db.session.query(User).filter_by(email=email).first():
        return api_error(
            409,
            "email_taken",
            "This email is already registered. Try logging in instead.",
        )
    if _phone_is_registered(phone):
        return api_error(
            409,
            "phone_taken",
            "This phone number is already registered to another account.",
        )

    user = User(name=name, email=email, phone=phone)
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        if db.session.query(User).filter_by(email=email).first():
            return api_error(
                409,
                "email_taken",
                "This email is already registered. Try logging in instead.",
            )
        if _phone_is_registered(phone):
            return api_error(
                409,
                "phone_taken",
                "This phone number is already registered to another account.",
            )
        raise

    return jsonify({
        "message": "User registered successfully",
        "user": user.to_dict(),
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}

    email_value = data.get("email")
    password = data.get("password")
    if (
        not isinstance(email_value, str)
        or not email_value.strip()
        or not isinstance(password, str)
        or not password
    ):
        return api_error(400, "missing_fields", "Enter your email and password.")

    email = email_value.strip().lower()
    user = db.session.query(User).filter_by(email=email).first()
    if user is None:
        return api_error(
            401,
            "email_not_found",
            "No account found with that email. Check the spelling or register.",
        )
    if not user.check_password(password):
        return api_error(
            401,
            "wrong_password",
            "Incorrect password. Try again or reset your password.",
        )

    return jsonify({
        "message": "Login successful",
        "user": user.to_dict(),
    }), 200


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}

    email_value = data.get("email")
    phone_value = data.get("phone")
    password = data.get("new_password")
    if (
        not isinstance(email_value, str)
        or not email_value.strip()
        or not isinstance(phone_value, str)
        or not phone_value.strip()
        or not isinstance(password, str)
        or not password
    ):
        return api_error(400, "missing_fields", "Enter your email, phone number and new password.")
    if not 8 <= len(password) <= 128:
        return api_error(400, "weak_password", "Password must be 8 to 128 characters.")

    email = email_value.strip().lower()
    user = db.session.query(User).filter_by(email=email).first()
    if user is None:
        return api_error(404, "email_not_found", "No account found with that email.")

    submitted_phone = normalize_kenyan_phone(phone_value)
    stored_phone = normalize_kenyan_phone(user.phone)
    if submitted_phone is None or submitted_phone != stored_phone:
        return api_error(
            400,
            "phone_mismatch",
            "That phone number does not match this account.",
        )

    user.set_password(password)
    db.session.commit()
    return jsonify({"message": "Password updated. You can now log in."}), 200
