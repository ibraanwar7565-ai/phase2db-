#!/usr/bin/env python3
"""Fill the database with realistic SmartPesa demo data.

Usage (from the server/ folder):
    python seed.py          # asks you to type SEED before writing anything
    python seed.py --yes    # no prompt (for scripts)

Safe to run again: demo users (emails ending in @smartpesa.local) are deleted
and recreated each time, together with their budgets and transactions.
Real users are never touched.

All demo users log in with password: DemoPass123!
"""

import random
import string
import sys
from datetime import datetime, timedelta, timezone

from extensions import db
from models import Budget, Transaction, User

DEMO_EMAIL_DOMAIN = "@smartpesa.local"
DEMO_PASSWORD = "DemoPass123!"

DEMO_USERS = [
    {"name": "Wanjiku Kamau", "email": "wanjiku" + DEMO_EMAIL_DOMAIN, "phone": "+254700100001"},
    {"name": "Otieno Odhiambo", "email": "otieno" + DEMO_EMAIL_DOMAIN, "phone": "+254700100002"},
    {"name": "Amina Hassan", "email": "amina" + DEMO_EMAIL_DOMAIN, "phone": "+254700100003"},
]

# Monthly budget limits in KES (converted to cents when saved).
BUDGET_LIMITS_KES = {
    "Food": 15_000,
    "Rent": 25_000,
    "Transport": 6_000,
    "Airtime": 1_500,
    "Utilities": 4_000,
    "Entertainment": 3_000,
}

# (description, transaction_type, min KES, max KES, times per month)
SPENDING = {
    "Food": [
        ("Naivas Supermarket", "till", 400, 3_500, 4),
        ("Quickmart", "till", 300, 2_500, 3),
        ("Mama Mboga", "send_money", 100, 600, 5),
        ("Java House", "till", 450, 1_200, 2),
    ],
    "Rent": [("Rent - Kilimani Apartments", "paybill", 25_000, 25_000, 1)],
    "Transport": [
        ("Matatu fare", "send_money", 50, 150, 8),
        ("Uber trip", "other", 300, 900, 3),
        ("Bolt trip", "other", 250, 800, 2),
    ],
    "Airtime": [
        ("Safaricom airtime", "airtime", 50, 300, 4),
        ("Safaricom data bundle", "airtime", 99, 500, 2),
    ],
    "Utilities": [
        ("KPLC tokens", "paybill", 500, 1_500, 2),
        ("Nairobi Water", "paybill", 600, 1_200, 1),
        ("Zuku internet", "paybill", 2_499, 2_499, 1),
    ],
    "Entertainment": [
        ("Showmax subscription", "paybill", 450, 450, 1),
        ("Movie - Century Cinemax", "till", 600, 1_200, 1),
        ("Weekend outing", "send_money", 500, 2_000, 1),
    ],
}

# Each user spends a different share of their budget so the analytics page has
# both under-budget and over-budget categories to show.
SPENDING_STYLE = {
    "wanjiku": 0.8,   # careful spender
    "otieno": 1.15,   # overspends on most things
    "amina": 1.0,     # roughly on budget
}


def mpesa_code(rng, used):
    """A unique 10-character M-Pesa style confirmation code, e.g. 'SJK3XY12AB'."""
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "S" + "".join(rng.choice(alphabet) for _ in range(9))
        if code not in used:
            used.add(code)
            return code


def month_start(day):
    return day.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def previous_month(day):
    return month_start(month_start(day) - timedelta(days=1))


def random_time_in_month(rng, start, until):
    """A random moment between the 1st of the month and `until` (or month end)."""
    next_month = month_start(start + timedelta(days=32))
    end = min(next_month, until)
    seconds = max(int((end - start).total_seconds()), 1)
    return start + timedelta(seconds=rng.randrange(seconds))


def remove_demo_data():
    """Delete demo users; their budgets and transactions cascade with them."""
    demo_users = User.query.filter(User.email.like("%" + DEMO_EMAIL_DOMAIN)).all()
    for user in demo_users:
        db.session.delete(user)
    db.session.flush()
    return len(demo_users)


def seed(now=None, rng_seed=42):
    """Create demo users with two months of budgets and transactions.

    Must be called inside an app context. Returns a summary dict.
    """
    now = now or datetime.now(timezone.utc)
    rng = random.Random(rng_seed)
    used_codes = {code for (code,) in db.session.query(Transaction.mpesa_code) if code}

    removed = remove_demo_data()
    months = [previous_month(now), month_start(now)]
    counts = {"users": 0, "budgets": 0, "transactions": 0}

    for info in DEMO_USERS:
        user = User(name=info["name"], email=info["email"], phone=info["phone"])
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        counts["users"] += 1

        style = SPENDING_STYLE[info["email"].split("@")[0]]

        for start in months:
            is_current = start == month_start(now)
            # Only part of the current month has happened, so spend less of it.
            share_of_month = now.day / 31 if is_current else 1.0

            for category, limit_kes in BUDGET_LIMITS_KES.items():
                budget = Budget(
                    user=user,
                    category=category,
                    limit_cents=limit_kes * 100,
                    month=start.strftime("%Y-%m"),
                )
                db.session.add(budget)
                counts["budgets"] += 1

                for description, kind, low, high, per_month in SPENDING[category]:
                    times = round(per_month * style * share_of_month)
                    if category == "Rent" and not is_current:
                        times = 1  # rent is always paid in full months
                    for _ in range(times):
                        kes = rng.randint(low, high) if low != high else low
                        db.session.add(Transaction(
                            user=user,
                            budget=budget,
                            description=description,
                            amount_cents=kes * 100,
                            transaction_type=kind,
                            mpesa_code=mpesa_code(rng, used_codes),
                            occurred_at=random_time_in_month(rng, start, now),
                        ))
                        counts["transactions"] += 1

        # A couple of payments that aren't linked to any budget.
        for description, kind, kes in [("Sent to family", "send_money", 2_000),
                                       ("Agent withdrawal", "withdrawal", 3_000)]:
            db.session.add(Transaction(
                user=user,
                description=description,
                amount_cents=kes * 100,
                transaction_type=kind,
                mpesa_code=mpesa_code(rng, used_codes),
                occurred_at=random_time_in_month(rng, months[0], now),
            ))
            counts["transactions"] += 1

    db.session.commit()
    counts["removed_users"] = removed
    counts["months"] = [m.strftime("%Y-%m") for m in months]
    return counts


def main():
    from app import create_app

    app = create_app()
    with app.app_context():
        print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        if "--yes" not in sys.argv:
            answer = input(
                "This replaces all demo users (*@smartpesa.local) and their data. "
                "Type SEED to continue: "
            )
            if answer.strip() != "SEED":
                print("Seeding cancelled.")
                return

        try:
            summary = seed()
        except Exception:
            db.session.rollback()
            raise

        print(f"Removed {summary['removed_users']} old demo user(s).")
        print(
            f"Created {summary['users']} users, {summary['budgets']} budgets and "
            f"{summary['transactions']} transactions for {', '.join(summary['months'])}."
        )
        print(f"Log in as e.g. wanjiku{DEMO_EMAIL_DOMAIN} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
