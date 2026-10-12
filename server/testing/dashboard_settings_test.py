from models import Budget, Transaction
from extensions import db


def test_dashboard_returns_user_totals_budgets_and_recent_transactions(app, user):
    budget = Budget(
        user=user,
        category="Food",
        limit_cents=50000,
        month="2026-10",
    )
    db.session.add(budget)
    db.session.add(
        Transaction(
            user=user,
            budget=budget,
            description="Groceries",
            amount_cents=12500,
            transaction_type="till",
        )
    )
    db.session.commit()

    response = app.test_client().get(f"/api/users/{user.id}/dashboard")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["user"]["id"] == user.id
    assert payload["summary"] == {
        "total_budget_cents": 50000,
        "total_spent_cents": 12500,
        "remaining_budget_cents": 37500,
        "budget_count": 1,
        "transaction_count": 1,
    }
    assert payload["budgets"][0]["category"] == "Food"
    assert payload["recent_transactions"][0]["description"] == "Groceries"


def test_settings_returns_user_and_budget_categories(app, user):
    db.session.add(
        Budget(
            user=user,
            category="Transport",
            limit_cents=10000,
            month="2026-10",
        )
    )
    db.session.commit()

    response = app.test_client().get(f"/api/users/{user.id}/settings")

    assert response.status_code == 200
    assert response.get_json() == {
        "user": user.to_dict(),
        "currency": "KES",
        "categories": ["Transport"],
        "category_records": [],
    }


def test_dashboard_and_settings_return_404_for_unknown_user(app):
    client = app.test_client()

    assert client.get("/api/users/999/dashboard").status_code == 404
    assert client.get("/api/users/999/settings").status_code == 404


def test_settings_can_update_currency_and_manage_categories(app, user):
    client = app.test_client()

    currency_response = client.patch(
        f"/api/users/{user.id}/settings", json={"currency": "USD"}
    )
    assert currency_response.status_code == 200
    assert currency_response.get_json()["currency"] == "USD"

    category_response = client.post(
        f"/api/users/{user.id}/settings/categories", json={"name": "Health"}
    )
    assert category_response.status_code == 201
    category_id = category_response.get_json()["id"]

    settings_response = client.get(f"/api/users/{user.id}/settings")
    assert settings_response.get_json()["categories"] == ["Health"]
    assert settings_response.get_json()["category_records"][0]["id"] == category_id

    assert (
        client.post(
            f"/api/users/{user.id}/settings/categories", json={"name": "health"}
        ).status_code
        == 409
    )
    assert (
        client.delete(
            f"/api/users/{user.id}/settings/categories/{category_id}"
        ).status_code
        == 204
    )
    assert (
        client.patch(
            f"/api/users/{user.id}/settings", json={"currency": "XYZ"}
        ).status_code
        == 400
    )


def test_api_allows_configured_frontend_origin(app):
    response = app.test_client().get(
        "/api/health", headers={"Origin": "http://localhost:5173"}
    )
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
