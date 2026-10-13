"""add monetary and data check constraints

Revision ID: e0a290fb010f
Revises: f85b57d8ee14
Create Date: 2026-10-13 06:19:22.575587

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e0a290fb010f'
down_revision = 'f85b57d8ee14'
branch_labels = None
depends_on = None


# Kept in sync with MAX_BUDGET_CENTS / MAX_TRANSACTION_CENTS in models.py.
CONSTRAINTS = [
    ("users", "ck_users_name_not_blank", "length(trim(name)) > 0"),
    ("users", "ck_users_email_has_at", "email LIKE '%_@_%'"),
    ("budgets", "ck_budgets_limit_max", "limit_cents <= 1000000000"),
    ("budgets", "ck_budgets_category_not_blank", "length(trim(category)) > 0"),
    (
        "budgets",
        "ck_budgets_month_format",
        "length(month) = 7 AND substr(month, 5, 1) = '-' "
        "AND substr(month, 6, 2) BETWEEN '01' AND '12'",
    ),
    ("transactions", "ck_transactions_amount_max", "amount_cents <= 100000000"),
    ("transactions", "ck_transactions_description_not_blank", "length(trim(description)) > 0"),
]


def upgrade():
    for table, name, condition in CONSTRAINTS:
        op.create_check_constraint(op.f(name), table, condition)


def downgrade():
    for table, name, _ in reversed(CONSTRAINTS):
        op.drop_constraint(op.f(name), table, type_="check")
