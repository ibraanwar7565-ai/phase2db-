from datetime import datetime, timezone

from models import Budget, Transaction, User
from seed import DEMO_PASSWORD, seed

NOW = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)


def test_seed_creates_two_months_of_data(db):
    summary = seed(now=NOW)

    assert summary["users"] == 3
    assert summary["months"] == ["2026-09", "2026-10"]
    assert User.query.count() == 3
    assert Budget.query.count() == 3 * 2 * 6
    assert Transaction.query.count() == summary["transactions"] > 100


def test_seed_data_is_realistic(db):
    seed(now=NOW)

    wanjiku = User.query.filter_by(email="wanjiku@smartpesa.local").one()
    assert wanjiku.check_password(DEMO_PASSWORD)

    for txn in Transaction.query:
        assert txn.amount_cents > 0
        assert txn.amount_cents % 100 == 0          # whole shillings
        assert len(txn.mpesa_code) == 10
        assert txn.occurred_at.replace(tzinfo=timezone.utc) <= NOW
        if txn.budget is not None:
            assert txn.budget.user_id == txn.user_id
            assert txn.occurred_at.strftime("%Y-%m") == txn.budget.month


def test_seed_has_overspent_and_underspent_budgets(db):
    seed(now=NOW)

    september = Budget.query.filter_by(month="2026-09").all()
    assert any(b.spent_cents() > b.limit_cents for b in september)
    assert any(b.spent_cents() < b.limit_cents for b in september)


def test_seed_can_run_twice_and_keeps_real_users(db, user):
    seed(now=NOW)
    first = Transaction.query.count()
    summary = seed(now=NOW)

    assert summary["removed_users"] == 3
    assert Transaction.query.count() == first
    assert db.session.get(User, user.id) is not None   # fixture user untouched
