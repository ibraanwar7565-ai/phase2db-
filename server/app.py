#!/usr/bin/env python3

from flask import Flask, jsonify, request
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from config import Config
from extensions import db, migrate
import models  # noqa: F401  (registers the models so Flask-Migrate can see them)
from models import Budget, Category, Transaction, User


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin == app.config["FRONTEND_ORIGIN"]:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PATCH, PUT, DELETE, OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.vary.add("Origin")
        return response

    @app.get("/api/health")
    def health():
        """Confirms the API is up and can reach the database."""
        db.session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}, 200

    @app.get("/api/users/<int:user_id>/dashboard")
    def dashboard(user_id):
        user = db.session.get(User, user_id)
        if user is None:
            return jsonify({"error": "User not found."}), 404

        budgets = (
            Budget.query.filter_by(user_id=user_id)
            .order_by(Budget.month.desc(), Budget.category.asc())
            .all()
        )
        transactions = (
            Transaction.query.filter_by(user_id=user_id)
            .order_by(Transaction.occurred_at.desc(), Transaction.id.desc())
            .all()
        )
        total_budget_cents = sum(budget.limit_cents for budget in budgets)
        total_spent_cents = sum(transaction.amount_cents for transaction in transactions)

        return jsonify(
            {
                "user": user.to_dict(),
                "summary": {
                    "total_budget_cents": total_budget_cents,
                    "total_spent_cents": total_spent_cents,
                    "remaining_budget_cents": total_budget_cents - total_spent_cents,
                    "budget_count": len(budgets),
                    "transaction_count": len(transactions),
                },
                "budgets": [budget.to_dict() for budget in budgets],
                "recent_transactions": [
                    transaction.to_dict() for transaction in transactions[:5]
                ],
            }
        )

    @app.get("/api/users/<int:user_id>/settings")
    def settings(user_id):
        user = db.session.get(User, user_id)
        if user is None:
            return jsonify({"error": "User not found."}), 404

        categories = (
            db.session.query(Budget.category)
            .filter_by(user_id=user_id)
            .distinct()
            .order_by(Budget.category.asc())
            .all()
        )
        saved_categories = Category.query.filter_by(user_id=user_id).order_by(
            Category.name.asc()
        ).all()
        category_names = sorted(
            {category for (category,) in categories}
            | {category.name for category in saved_categories},
            key=str.casefold,
        )
        return jsonify(
            {
                "user": user.to_dict(),
                "currency": user.currency,
                "categories": category_names,
                "category_records": [
                    category.to_dict() for category in saved_categories
                ],
            }
        )

    @app.patch("/api/users/<int:user_id>/settings")
    def update_settings(user_id):
        user = db.session.get(User, user_id)
        if user is None:
            return jsonify({"error": "User not found."}), 404

        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or not payload:
            return jsonify({"error": "Provide at least one setting to update."}), 400

        if "currency" in payload:
            currency = payload["currency"]
            if not isinstance(currency, str) or currency not in {
                "KES",
                "USD",
                "EUR",
                "GBP",
            }:
                return jsonify({"error": "currency must be KES, USD, EUR, or GBP."}), 400
            user.currency = currency

        db.session.commit()
        return jsonify({"user": user.to_dict(), "currency": user.currency})

    @app.post("/api/users/<int:user_id>/settings/categories")
    def create_category(user_id):
        user = db.session.get(User, user_id)
        if user is None:
            return jsonify({"error": "User not found."}), 404

        payload = request.get_json(silent=True)
        name_value = payload.get("name") if isinstance(payload, dict) else None
        if not isinstance(name_value, str):
            return jsonify({"error": "name is required."}), 400
        name = name_value.strip()
        if not name:
            return jsonify({"error": "name is required."}), 400
        if len(name) > 50:
            return jsonify({"error": "name must be 50 characters or fewer."}), 400

        duplicate = Category.query.filter_by(user_id=user_id).all()
        if any(category.name.casefold() == name.casefold() for category in duplicate):
            return jsonify({"error": "That category already exists."}), 409

        category = Category(user=user, name=name)
        db.session.add(category)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "That category already exists."}), 409
        return jsonify(category.to_dict()), 201

    @app.delete("/api/users/<int:user_id>/settings/categories/<int:category_id>")
    def delete_category(user_id, category_id):
        category = Category.query.filter_by(id=category_id, user_id=user_id).first()
        if category is None:
            return jsonify({"error": "Category not found."}), 404

        db.session.delete(category)
        db.session.commit()
        return "", 204

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
