"""create offer table

Revision ID: 0001_create_offer_table
Revises: 
Create Date: 2026-03-20
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_create_offer_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "offer",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=120), nullable=False),
        sa.Column("location", sa.String(length=120), nullable=False),
        sa.Column("base_salary", sa.Float(), nullable=False),
        sa.Column("annual_bonus", sa.Float(), nullable=False),
        sa.Column("annual_equity", sa.Float(), nullable=False),
        sa.Column("sign_on_bonus", sa.Float(), nullable=False),
        sa.Column("col_index", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("offer")
