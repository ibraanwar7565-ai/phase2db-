import re
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from errors import api_error
from extensions import db
from models import (Transaction, Budget, User,
                    TRANSACTION_TYPES, MAX_TRANSACTION_CENTS)
from utils import is_int

transactions_bp = Blueprint("transactions", __name__, url_prefix="/api/transactions")

MONTH_RE = re.compile(r"(\d{4})-(0[1-9]|1[0-2])")


def parse_datetime(value):
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@transactions_bp.route("", methods=["POST"])
def create_transaction():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return api_error(400, "bad_request", "Request body must be valid JSON")

    user_id = data.get("user_id")
    budget_id = data.get("budget_id")
    description = data.get("description")
    amount_cents = data.get("amount_cents")
    transaction_type = data.get("transaction_type", "other")
    mpesa_code = data.get("mpesa_code") or None
    occurred_at = data.get("occurred_at")

    if not is_int(user_id) or user_id <= 0:
        return api_error(400, "validation_error", "A valid user_id is required")

    description = description.strip() if isinstance(description, str) else ""
    if not description or len(description) > 200:
        return api_error(400, "validation_error", "description must contain 1-200 characters")

    if not is_int(amount_cents) or not 0 < amount_cents <= MAX_TRANSACTION_CENTS:
        return api_error(400, "validation_error",
                         f"amount_cents must be an integer between 1 and {MAX_TRANSACTION_CENTS}")

    if transaction_type not in TRANSACTION_TYPES:
        return api_error(400, "validation_error",
                         f"transaction_type must be one of: {', '.join(TRANSACTION_TYPES)}")

    if mpesa_code is not None and (not isinstance(mpesa_code, str) or len(mpesa_code) > 20):
        return api_error(400, "validation_error", "mpesa_code must be at most 20 characters")

    when = None
    if occurred_at is not None:
        when = parse_datetime(occurred_at)
        if when is None:
            return api_error(400, "validation_error",
                             "occurred_at must be an ISO date, e.g. 2026-10-13")

    if db.session.get(User, user_id) is None:
        return api_error(404, "not_found", "User does not exist")

    if budget_id is not None:
        if not is_int(budget_id) or budget_id <= 0:
            return api_error(400, "validation_error", "Invalid budget_id")
        budget = db.session.get(Budget, budget_id)
        if budget is None or budget.user_id != user_id:
            return api_error(404, "not_found", "Budget does not exist for this user")

    transaction = Transaction(
        user_id=user_id, budget_id=budget_id, description=description,
        amount_cents=amount_cents, transaction_type=transaction_type,
        mpesa_code=mpesa_code,
    )
    if when:
        transaction.occurred_at = when

    try:
        db.session.add(transaction)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return api_error(409, "conflict",
                         "Transaction conflicts with an existing record (duplicate M-Pesa code?)")

    return jsonify({"message": "Transaction created successfully",
                    "transaction": transaction.to_dict()}), 201


@transactions_bp.route("", methods=["GET"])
def list_transactions():
    user_id = request.args.get("user_id", type=int)
    if not user_id or user_id <= 0:
        return api_error(400, "validation_error", "A valid user_id is required")

    query = Transaction.query.filter_by(user_id=user_id)

    budget_id = request.args.get("budget_id", type=int)
    if budget_id is not None:
        query = query.filter_by(budget_id=budget_id)

    month = request.args.get("month")
    if month:
        m = MONTH_RE.fullmatch(month)
        if not m:
            return api_error(400, "validation_error", "month must use YYYY-MM format")
        year, mon = int(m.group(1)), int(m.group(2))
        start = datetime(year, mon, 1, tzinfo=timezone.utc)
        end = datetime(year + (mon == 12), mon % 12 + 1, 1, tzinfo=timezone.utc)
        query = query.filter(Transaction.occurred_at >= start,
                             Transaction.occurred_at < end)

    transactions = query.order_by(Transaction.occurred_at.desc()).all()
    return jsonify({"transactions": [t.to_dict() for t in transactions]}), 200


@transactions_bp.route("/<int:transaction_id>", methods=["GET"])
def get_transaction(transaction_id):
    transaction = db.session.get(Transaction, transaction_id)
    if transaction is None:
        return api_error(404, "not_found", "Transaction not found")
    return jsonify({"transaction": transaction.to_dict()}), 200


@transactions_bp.route("/<int:transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):
    transaction = db.session.get(Transaction, transaction_id)
    if transaction is None:
        return api_error(404, "not_found", "Transaction not found")
    db.session.delete(transaction)
    db.session.commit()
    return "", 204