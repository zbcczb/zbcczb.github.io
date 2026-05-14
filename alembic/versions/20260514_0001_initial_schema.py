"""initial schema

Revision ID: 20260514_0001
Revises:
Create Date: 2026-05-14 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260514_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "factories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_factories_code"), "factories", ["code"], unique=True)
    op.create_index(op.f("ix_factories_id"), "factories", ["id"], unique=False)

    op.create_table(
        "machines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("machine_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("factory_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["factory_id"], ["factories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_machines_id"), "machines", ["id"], unique=False)
    op.create_index(op.f("ix_machines_machine_id"), "machines", ["machine_id"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("full_name", sa.String(length=128), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("factory_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["factory_id"], ["factories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "alarm_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("machine_id", sa.Integer(), nullable=False),
        sa.Column("alarm_code", sa.String(length=64), nullable=False),
        sa.Column("message", sa.String(length=255), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alarm_records_alarm_code"), "alarm_records", ["alarm_code"], unique=False)
    op.create_index(op.f("ix_alarm_records_id"), "alarm_records", ["id"], unique=False)
    op.create_index(op.f("ix_alarm_records_machine_id"), "alarm_records", ["machine_id"], unique=False)
    op.create_index(op.f("ix_alarm_records_occurred_at"), "alarm_records", ["occurred_at"], unique=False)

    op.create_table(
        "machine_statuses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("machine_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("rpm", sa.Integer(), nullable=False),
        sa.Column("current_stitches", sa.Integer(), nullable=False),
        sa.Column("finished_pieces", sa.Integer(), nullable=False),
        sa.Column("work_hours", sa.Float(), nullable=False),
        sa.Column("alarm_code", sa.String(length=64), nullable=True),
        sa.Column("pattern_id", sa.String(length=64), nullable=True),
        sa.Column("device_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_machine_statuses_device_timestamp"), "machine_statuses", ["device_timestamp"], unique=False)
    op.create_index(op.f("ix_machine_statuses_id"), "machine_statuses", ["id"], unique=False)
    op.create_index(op.f("ix_machine_statuses_machine_id"), "machine_statuses", ["machine_id"], unique=False)
    op.create_index(op.f("ix_machine_statuses_received_at"), "machine_statuses", ["received_at"], unique=False)
    op.create_index(op.f("ix_machine_statuses_status"), "machine_statuses", ["status"], unique=False)

    op.create_table(
        "production_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("machine_id", sa.Integer(), nullable=False),
        sa.Column("pattern_id", sa.String(length=64), nullable=True),
        sa.Column("production_date", sa.Date(), nullable=False),
        sa.Column("stitches", sa.Integer(), nullable=False),
        sa.Column("finished_pieces", sa.Integer(), nullable=False),
        sa.Column("work_hours", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_production_records_id"), "production_records", ["id"], unique=False)
    op.create_index(op.f("ix_production_records_machine_id"), "production_records", ["machine_id"], unique=False)
    op.create_index(op.f("ix_production_records_production_date"), "production_records", ["production_date"], unique=False)
    op.create_index(op.f("ix_production_records_recorded_at"), "production_records", ["recorded_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_production_records_recorded_at"), table_name="production_records")
    op.drop_index(op.f("ix_production_records_production_date"), table_name="production_records")
    op.drop_index(op.f("ix_production_records_machine_id"), table_name="production_records")
    op.drop_index(op.f("ix_production_records_id"), table_name="production_records")
    op.drop_table("production_records")
    op.drop_index(op.f("ix_machine_statuses_status"), table_name="machine_statuses")
    op.drop_index(op.f("ix_machine_statuses_received_at"), table_name="machine_statuses")
    op.drop_index(op.f("ix_machine_statuses_machine_id"), table_name="machine_statuses")
    op.drop_index(op.f("ix_machine_statuses_id"), table_name="machine_statuses")
    op.drop_index(op.f("ix_machine_statuses_device_timestamp"), table_name="machine_statuses")
    op.drop_table("machine_statuses")
    op.drop_index(op.f("ix_alarm_records_occurred_at"), table_name="alarm_records")
    op.drop_index(op.f("ix_alarm_records_machine_id"), table_name="alarm_records")
    op.drop_index(op.f("ix_alarm_records_id"), table_name="alarm_records")
    op.drop_index(op.f("ix_alarm_records_alarm_code"), table_name="alarm_records")
    op.drop_table("alarm_records")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_machines_machine_id"), table_name="machines")
    op.drop_index(op.f("ix_machines_id"), table_name="machines")
    op.drop_table("machines")
    op.drop_index(op.f("ix_factories_id"), table_name="factories")
    op.drop_index(op.f("ix_factories_code"), table_name="factories")
    op.drop_table("factories")
