"""add user preferences and categories

Revision ID: 4b7a2c9d31ef
Revises: f85b57d8ee14
Create Date: 2026-10-12

"""
from alembic import op
import sqlalchemy as sa


revision = "4b7a2c9d31ef"
down_revision = "f85b57d8ee14"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "currency",
                sa.String(length=3),
                server_default="KES",
                nullable=False,
            )
        )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_categories_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.UniqueConstraint("user_id", "name", name="uq_categories_user_name"),
    )
    with op.batch_alter_table("categories", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_categories_user_id"), ["user_id"], unique=False
        )


def downgrade():
    with op.batch_alter_table("categories", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_categories_user_id"))

    op.drop_table("categories")
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("currency")
