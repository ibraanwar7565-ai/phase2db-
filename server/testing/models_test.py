import pytest
from sqlalchemy.exc import IntegrityError

from models import Budget, Transaction, User


def test_health_route(app):
    response = app.test_client().get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["database"] == "connected"


def test_password_is_hashed_and_hidden(user):
    assert user.password_hash != "secret123"
    assert user.check_password("secret123")
    assert not user.check_password("wrong")
    assert "password_hash" not in user.to_dict()


def test_email_must_be_unique(db, user):
    dup = User(name="Other", email="wanjiku@example.com")
    dup.set_password("x")
    db.session.add(dup)
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_budget_tracks_spent_and_remaining(db, user):
    food = Budget(user=user, category="Food", limit_cents=500000, month="2026-10")
    db.session.add_all([
        food,
        Transaction(user=user, budget=food, description="Naivas", amount_cents=125050,
                    transaction_type="till", mpesa_code="SJK3XY12AB"),
        Transaction(user=user, budget=food, description="Lunch", amount_cents=35000,
                    transaction_type="send_money"),
    ])
    db.session.commit()

    data = food.to_dict()
    assert data["spent_cents"] == 160050
    assert data["remaining_cents"] == 339950


def test_budget_limit_cannot_be_negative(db, user):
    db.session.add(Budget(user=user, category="Rent", limit_cents=-1, month="2026-10"))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_one_budget_per_category_per_month(db, user):
    db.session.add(Budget(user=user, category="Food", limit_cents=100, month="2026-10"))
    db.session.commit()
    db.session.add(Budget(user=user, category="Food", limit_cents=200, month="2026-10"))
    with pytest.raises(IntegrityError):
        db.session.commit()


@pytest.mark.parametrize("amount", [0, -500])
def test_transaction_amount_must_be_positive(db, user, amount):
    db.session.add(Transaction(user=user, description="Bad", amount_cents=amount))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_transaction_type_must_be_known(db, user):
    db.session.add(Transaction(user=user, description="Bad", amount_cents=100,
                               transaction_type="bitcoin"))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_transaction_requires_existing_user(db):
    db.session.add(Transaction(user_id=999, description="Ghost", amount_cents=100))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_deleting_budget_keeps_transactions(db, user):
    airtime = Budget(user=user, category="Airtime", limit_cents=100000, month="2026-10")
    txn = Transaction(user=user, budget=airtime, description="Safaricom bundle",
                      amount_cents=10000, transaction_type="airtime")
    db.session.add_all([airtime, txn])
    db.session.commit()

    db.session.delete(airtime)
    db.session.commit()
    db.session.expire_all()

    kept = db.session.get(Transaction, txn.id)
    assert kept is not None
    assert kept.budget_id is None


def test_deleting_user_removes_their_data(db, user):
    budget = Budget(user=user, category="Food", limit_cents=100, month="2026-10")
    db.session.add_all([budget, Transaction(user=user, budget=budget, description="x",
                                            amount_cents=50)])
    db.session.commit()

    db.session.delete(user)
    db.session.commit()

    assert Budget.query.count() == 0
    assert Transaction.query.count() == 0
