from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    phone = data.get("phone", "").strip()
    password = data.get("password", "")

    if not all([name, email, phone, password]):
        return jsonify({
            "error": "Name, email, phone and password are required"
        }), 400

    if not isinstance(password, str) or len(password) < 8:
        return jsonify({
            "error": "Password must be at least 8 characters"
        }), 400

    user = User(
        name=name,
        email=email,
        phone=phone
    )
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Email or phone number is already registered"
        }), 409

    return jsonify({
        "message": "User registered successfully",
        "user": user.to_dict()
    }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    user = db.session.query(User).filter_by(email=email).first()

    if user is None or not user.check_password(password):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    return jsonify({
        "message": "Login successful",
        "user": user.to_dict()
    }), 200