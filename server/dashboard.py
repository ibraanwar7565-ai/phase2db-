import re
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify

from errors import api_error
from extensions import db
from models import Budget, Transaction, User

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.route("", methods=["GET"])
def get_dashboard():
    user_id = request.args.get("user_id", type=int)
    if not user_id or user_id <= 0:
        return api_error(400, "validation_error", "A valid user_id is required")

    month = request.args.get("month") or datetime.now(timezone.utc).strftime("%Y-%m")
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month):
        return api_error(400, "validation_error", "month must use YYYY-MM format")

    if db.session.get(User, user_id) is None:
        return api_error(404, "not_found", "User not found")

    budgets = (Budget.query.filter_by(user_id=user_id, month=month)
               .order_by(Budget.category).all())

    total_budget = sum(b.limit_cents for b in budgets)
    total_spent = sum(b.spent_cents() for b in budgets)
    tx_count = sum(len(b.transactions) for b in budgets)

    budget_rows = []
    for b in budgets:
        row = b.to_dict()
        row["percent_used"] = (round(row["spent_cents"] * 100 / b.limit_cents, 1)
                               if b.limit_cents else None)
        row["over_budget"] = row["remaining_cents"] < 0
        budget_rows.append(row)

    recent = (Transaction.query.filter_by(user_id=user_id)
              .order_by(Transaction.occurred_at.desc()).limit(5).all())

    return jsonify({
        "month": month,
        "total_budget_cents": total_budget,
        "total_spent_cents": total_spent,
        "remaining_cents": total_budget - total_spent,
        "transaction_count": tx_count,
        "budgets": budget_rows,
        "recent_transactions": [t.to_dict() for t in recent],
    }), 200