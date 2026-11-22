"""Phase 1 core operational tables

Revision ID: 20261122_001
Revises:
Create Date: 2026-11-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261122_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_ref", sa.String(32), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("segment", sa.String(20), nullable=False),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("risk_profile", sa.String(20), nullable=False),
        sa.Column("onboarding_date", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("customer_ref"))

    op.create_table("accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_number", sa.String(32), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_type", sa.String(30), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("balance", sa.Numeric(18, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("last_activity_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("account_number"))

    op.create_table("devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_identifier", sa.String(100), nullable=False),
        sa.Column("device_type", sa.String(30), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("device_identifier"))

    op.create_table("beneficiaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("receiver_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("first_used_at", sa.DateTime(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["sender_account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["receiver_account_id"], ["accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sender_account_id", "receiver_account_id", name="uq_beneficiary_relationship"))

    op.create_table("transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", sa.String(64), nullable=False),
        sa.Column("sender_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("receiver_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("transaction_type", sa.String(30), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("source_location", sa.String(100), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True)),
        sa.Column("beneficiary_id", postgresql.UUID(as_uuid=True)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("processing_status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_transaction_positive_amount"),
        sa.ForeignKeyConstraint(["beneficiary_id"], ["beneficiaries.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
        sa.ForeignKeyConstraint(["receiver_account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["sender_account_id"], ["accounts.id"]),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("event_id"))
    op.create_index("ix_transactions_occurred_at", "transactions", ["occurred_at"])
    op.create_index("ix_transactions_accounts", "transactions", ["sender_account_id", "receiver_account_id"])


def downgrade():
    op.drop_index("ix_transactions_accounts", table_name="transactions")
    op.drop_index("ix_transactions_occurred_at", table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("beneficiaries")
    op.drop_table("devices")
    op.drop_table("accounts")
    op.drop_table("customers")
