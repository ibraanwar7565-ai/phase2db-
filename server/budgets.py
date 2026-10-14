import re

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from errors import api_error
from extensions import db
from models import Budget, MAX_BUDGET_CENTS

budgets_bp = Blueprint("budgets", __name__, url_prefix="/api/budgets")

MONTH_RE = re.compile(r"\d{4}-(0[1-9]|1[0-2])")


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def validate_fields(data, partial=False):
    """Validate budget fields. Returns (clean_dict, error_message)."""
    clean = {}

    if "category" in data or not partial:
        category = data.get("category")
        category = category.strip() if isinstance(category, str) else ""
        if not category or len(category) > 50:
            return None, "category must contain 1-50 characters"
        clean["category"] = category

    if "limit_cents" in data or not partial:
        limit = data.get("limit_cents")
        if not is_int(limit) or not 0 <= limit <= MAX_BUDGET_CENTS:
            return None, f"limit_cents must be an integer between 0 and {MAX_BUDGET_CENTS}"
        clean["limit_cents"] = limit

    if "month" in data or not partial:
        month = data.get("month")
        if not isinstance(month, str) or not MONTH_RE.fullmatch(month):
            return None, "month must use YYYY-MM format, e.g. 2026-10"
        clean["month"] = month

    return clean, None


@budgets_bp.route("", methods=["POST"])
def create_budget():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return api_error(400, "bad_request", "Request body must be valid JSON")

    user_id = data.get("user_id")
    if not is_int(user_id) or user_id <= 0:
        return api_error(400, "validation_error", "user_id must be a positive integer")

    clean, error = validate_fields(data)
    if error:
        return api_error(400, "validation_error", error)

    budget = Budget(user_id=user_id, **clean)
    try:
        db.session.add(budget)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return api_error(
            409, "conflict",
            "Budget already exists for this category and month, or user does not exist",
        )

    return jsonify({"message": "Budget created successfully",
                    "budget": budget.to_dict()}), 201


@budgets_bp.route("", methods=["GET"])
def list_budgets():
    user_id = request.args.get("user_id", type=int)
    month = request.args.get("month")

    if not user_id or user_id <= 0:
        return api_error(400, "validation_error", "A valid user_id is required")

    query = Budget.query.filter_by(user_id=user_id)
    if month:
        query = query.filter_by(month=month)

    budgets = query.order_by(Budget.month.desc(), Budget.category.asc()).all()
    return jsonify({"budgets": [b.to_dict() for b in budgets]}), 200


@budgets_bp.route("/<int:budget_id>", methods=["GET"])
def get_budget(budget_id):
    budget = db.session.get(Budget, budget_id)
    if budget is None:
        return api_error(404, "not_found", "Budget not found")
    return jsonify({"budget": budget.to_dict()}), 200


@budgets_bp.route("/<int:budget_id>", methods=["PUT"])
def update_budget(budget_id):
    budget = db.session.get(Budget, budget_id)
    if budget is None:
        return api_error(404, "not_found", "Budget not found")

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return api_error(400, "bad_request", "Provide at least one field to update")

    clean, error = validate_fields(data, partial=True)
    if error:
        return api_error(400, "validation_error", error)

    for field, value in clean.items():
        setattr(budget, field, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return api_error(409, "conflict",
                         "Another budget already uses this category and month")

    return jsonify({"message": "Budget updated successfully",
                    "budget": budget.to_dict()}), 200


@budgets_bp.route("/<int:budget_id>", methods=["DELETE"])
def delete_budget(budget_id):
    budget = db.session.get(Budget, budget_id)
    if budget is None:
        return api_error(404, "not_found", "Budget not found")

    db.session.delete(budget)
    db.session.commit()
    return "", 204