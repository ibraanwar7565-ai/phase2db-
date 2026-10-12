from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from extensions import db
from models import Budget

budgets_bp = Blueprint("budgets", __name__, url_prefix="/api/budgets")


@budgets_bp.route("", methods=["POST"])
def create_budget():
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    category = data.get("category")
    limit_cents = data.get("limit_cents")
    month = data.get("month")

    if not all([user_id, category, month]) or limit_cents is None:
        return jsonify({
            "error": "user_id, category, limit_cents and month are required"
        }), 400

    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        return jsonify({"error": "user_id must be a positive integer"}), 400

    if not isinstance(limit_cents, int) or isinstance(limit_cents, bool) or limit_cents < 0:
        return jsonify({"error": "limit_cents must be a non-negative integer"}), 400

    category = category.strip() if isinstance(category, str) else ""
    if not category or len(category) > 50:
        return jsonify({"error": "category must contain 1-50 characters"}), 400

    if not isinstance(month, str) or len(month) != 7:
        return jsonify({"error": "month must use YYYY-MM format"}), 400

    try:
        year, month_number = map(int, month.split("-"))
        if not 1 <= month_number <= 12 or year < 1:
            raise ValueError
    except ValueError:
        return jsonify({"error": "month must be a valid YYYY-MM date"}), 400

    budget = Budget(
        user_id=user_id,
        category=category,
        limit_cents=limit_cents,
        month=month,
    )

    try:
        db.session.add(budget)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Budget already exists for this category and month, or user does not exist"
        }), 409

    return jsonify({
        "message": "Budget created successfully",
        "budget": budget.to_dict(),
    }), 201


@budgets_bp.route("", methods=["GET"])
def list_budgets():
    user_id = request.args.get("user_id", type=int)
    month = request.args.get("month")

    if not user_id or user_id <= 0:
        return jsonify({"error": "A valid user_id is required"}), 400

    query = Budget.query.filter_by(user_id=user_id)

    if month:
        query = query.filter_by(month=month)

    budgets = query.order_by(Budget.month.desc(), Budget.category.asc()).all()

    return jsonify({
        "budgets": [budget.to_dict() for budget in budgets]
    }), 200