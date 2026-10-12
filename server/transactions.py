from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Transaction, Budget, User

transactions_bp = Blueprint(
    "transactions",
    __name__,
    url_prefix="/api/transactions"
)


@transactions_bp.route("", methods=["POST"])
def create_transaction():
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    budget_id = data.get("budget_id")
    description = data.get("description")
    amount_cents = data.get("amount_cents")
    transaction_type = data.get("transaction_type", "other")
    mpesa_code = data.get("mpesa_code") or None

    if (
        not isinstance(user_id, int)
        or isinstance(user_id, bool)
        or user_id <= 0
    ):
        return jsonify({"error": "A valid user_id is required"}), 400

    if not isinstance(description, str) or not description.strip():
        return jsonify({"error": "A description is required"}), 400

    description = description.strip()
    if len(description) > 200:
        return jsonify({"error": "Description cannot exceed 200 characters"}), 400

    if (
        not isinstance(amount_cents, int)
        or isinstance(amount_cents, bool)
        or amount_cents <= 0
    ):
        return jsonify({
            "error": "amount_cents must be a positive integer"
        }), 400

    if transaction_type not in (
        "paybill", "till", "send_money",
        "airtime", "withdrawal", "other"
    ):
        return jsonify({"error": "Invalid transaction_type"}), 400

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "User does not exist"}), 404

    budget = None
    if budget_id is not None:
        if (
            not isinstance(budget_id, int)
            or isinstance(budget_id, bool)
            or budget_id <= 0
        ):
            return jsonify({"error": "Invalid budget_id"}), 400

        budget = db.session.get(Budget, budget_id)

        if budget is None or budget.user_id != user_id:
            return jsonify({
                "error": "Budget does not exist for this user"
            }), 404

    if mpesa_code is not None:
        if not isinstance(mpesa_code, str) or len(mpesa_code) > 20:
            return jsonify({"error": "Invalid mpesa_code"}), 400

    transaction = Transaction(
        user_id=user_id,
        budget_id=budget_id,
        description=description,
        amount_cents=amount_cents,
        transaction_type=transaction_type,
        mpesa_code=mpesa_code,
    )

    try:
        db.session.add(transaction)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Transaction could not be saved; check the M-Pesa code"
        }), 409

    return jsonify({
        "message": "Transaction created successfully",
        "transaction": transaction.to_dict(),
    }), 201


@transactions_bp.route("", methods=["GET"])
def list_transactions():
    user_id = request.args.get("user_id", type=int)

    if not user_id or user_id <= 0:
        return jsonify({"error": "A valid user_id is required"}), 400

    query = Transaction.query.filter_by(user_id=user_id)

    budget_id = request.args.get("budget_id", type=int)
    if budget_id is not None:
        query = query.filter_by(budget_id=budget_id)

    transactions = query.order_by(
        Transaction.occurred_at.desc()
    ).all()

    return jsonify({
        "transactions": [
            transaction.to_dict()
            for transaction in transactions
        ]
    }), 200