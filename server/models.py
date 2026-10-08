from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db

# All money is stored as whole cents (integers) to avoid floating-point bugs.
# KES 1,250.50 is stored as 125050.

TRANSACTION_TYPES = ("paybill", "till", "send_money", "airtime", "withdrawal", "other")


def utc_now():
    return datetime.now(timezone.utc)


class User(db.Model):
    """A SmartPesa account holder."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    phone = db.Column(db.String(20), unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    # Deleting a user deletes their budgets and transactions too.
    budgets = db.relationship(
        "Budget", back_populates="user", cascade="all, delete-orphan"
    )
    transactions = db.relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        # password_hash is deliberately never returned.
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User {self.id} {self.email}>"


class Budget(db.Model):
    """A monthly spending limit for one category (Food, Rent, Airtime...)."""

    __tablename__ = "budgets"
    __table_args__ = (
        CheckConstraint("limit_cents >= 0", name="limit_not_negative"),
        # One "Food" budget per user per month.
        UniqueConstraint("user_id", "category", "month", name="uq_budgets_user_category_month"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category = db.Column(db.String(50), nullable=False)
    limit_cents = db.Column(db.Integer, nullable=False)
    # Budget period in "YYYY-MM" form, e.g. "2026-10".
    month = db.Column(db.String(7), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    user = db.relationship("User", back_populates="budgets")
    # Deleting a budget keeps its transactions; their budget_id becomes NULL.
    transactions = db.relationship(
        "Transaction", back_populates="budget", passive_deletes=True
    )

    def spent_cents(self):
        return sum(t.amount_cents for t in self.transactions)

    def to_dict(self):
        spent = self.spent_cents()
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category": self.category,
            "limit_cents": self.limit_cents,
            "spent_cents": spent,
            "remaining_cents": self.limit_cents - spent,
            "month": self.month,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Budget {self.id} {self.category} {self.month}>"


class Transaction(db.Model):
    """One expense, linked to the user who made it and (optionally) a budget."""

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="amount_positive"),
        CheckConstraint(
            "transaction_type IN ('" + "', '".join(TRANSACTION_TYPES) + "')",
            name="valid_type",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    budget_id = db.Column(
        db.Integer, db.ForeignKey("budgets.id", ondelete="SET NULL"), index=True
    )
    description = db.Column(db.String(200), nullable=False)
    amount_cents = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False, default="other")
    # M-Pesa confirmation code (e.g. "SJK3XY12AB"); empty for manual entries.
    mpesa_code = db.Column(db.String(20), unique=True)
    occurred_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    user = db.relationship("User", back_populates="transactions")
    budget = db.relationship("Budget", back_populates="transactions")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "budget_id": self.budget_id,
            "description": self.description,
            "amount_cents": self.amount_cents,
            "transaction_type": self.transaction_type,
            "mpesa_code": self.mpesa_code,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Transaction {self.id} {self.amount_cents}c>"
