from datetime import datetime, timezone

from app import create_app
from extensions import db
from models import User, Budget, Transaction


def seed_database():
    app = create_app()

    with app.app_context():
        # Require explicit confirmation before writing demo data.
        confirmation = input(
            "This will add demo data to the configured database. "
            "Type SEED to continue: "
        )

        if confirmation != "SEED":
            print("Seeding cancelled.")
            return

        # Find or create the demo user.
        email = "seed.user@smartpesa.local"
        user = User.query.filter_by(email=email).first()

        if user is None:
            user = User(
                name="SmartPesa Demo User",
                email=email,
            )
            user.set_password("DemoPass123!")
            db.session.add(user)
            db.session.flush()
            print("Created demo user.")
        else:
            print("Demo user already exists.")

        # Find or create a budget for the current month.
        month = datetime.now(timezone.utc).strftime("%Y-%m")

        budget = Budget.query.filter_by(
            user_id=user.id,
            category="Seed Demo Food",
            month=month,
        ).first()

        if budget is None:
            budget = Budget(
                user_id=user.id,
                category="Seed Demo Food",
                limit_cents=500000,  # KSh 5,000.00
                month=month,
            )
            db.session.add(budget)
            db.session.flush()
            print("Created demo budget.")
        else:
            print("Demo budget already exists.")

        # A stable confirmation code prevents duplicate transactions.
        code = "SEEDDEMO0001"
        transaction = Transaction.query.filter_by(
            mpesa_code=code
        ).first()

        if transaction is None:
            transaction = Transaction(
                user_id=user.id,
                budget_id=budget.id,
                description="Demo food purchase",
                amount_cents=12500,  # KSh 125.00
                transaction_type="other",
                mpesa_code=code,
            )
            db.session.add(transaction)
            print("Created demo transaction.")
        else:
            print("Demo transaction already exists.")

        try:
            db.session.commit()
            print("Seeding completed successfully.")
            print(f"Demo user ID: {user.id}")
            print(f"Budget ID: {budget.id}")
            print(f"Budget month: {month}")
        except Exception:
            db.session.rollback()
            raise


if __name__ == "__main__":
    seed_database()