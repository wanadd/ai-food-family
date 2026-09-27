"""Canonical Wave 7 asynchronous notifications and Telegram delivery boundary."""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260927_0018"
down_revision: str | None = "20260927_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    uid = postgresql.UUID(as_uuid=False)
    js = postgresql.JSONB()
    timestamp = sa.DateTime(timezone=True)

    op.create_table(
        "notification_preferences",
        sa.Column("preference_id", uid, primary_key=True),
        sa.Column("subject_kind", sa.String(16), nullable=False),
        sa.Column("subject_id", uid, nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("timezone", sa.String(64), nullable=True),
        sa.Column("quiet_hours_start", sa.String(5), nullable=True),
        sa.Column("quiet_hours_end", sa.String(5), nullable=True),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("request_hash", sa.String(128), nullable=False),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("subject_kind IN ('PERSON', 'HOUSEHOLD')", name="ck_notification_preferences_subject"),
        sa.CheckConstraint("channel <> ''", name="ck_notification_preferences_channel"),
        sa.UniqueConstraint("subject_kind", "subject_id", "channel", name="uq_notification_preferences_subject_channel"),
        sa.UniqueConstraint("subject_kind", "subject_id", "channel", "idempotency_key", name="uq_notification_preferences_idempotency"),
    )
    op.create_index("ix_notification_preferences_subject", "notification_preferences", ["subject_kind", "subject_id"])

    op.create_table(
        "notification_intents",
        sa.Column("intent_id", uid, primary_key=True),
        sa.Column("owner_domain", sa.String(64), nullable=False),
        sa.Column("aggregate_id", uid, nullable=False),
        sa.Column("intent_type", sa.String(96), nullable=False),
        sa.Column("subject_kind", sa.String(16), nullable=False),
        sa.Column("subject_id", uid, nullable=False),
        sa.Column("recipient_person_id", uid, nullable=True),
        sa.Column("recipient_household_id", uid, nullable=True),
        sa.Column("state", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("payload_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("navigation_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("available_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["recipient_person_id"], ["core_persons.person_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recipient_household_id"], ["core_households.household_id"], ondelete="SET NULL"),
        sa.CheckConstraint("subject_kind IN ('PERSON', 'HOUSEHOLD')", name="ck_notification_intents_subject"),
        sa.CheckConstraint("state IN ('pending', 'leased', 'succeeded', 'retryable', 'failed', 'dead-letter', 'manual-review')", name="ck_notification_intents_state"),
        sa.UniqueConstraint("owner_domain", "aggregate_id", "intent_type", "idempotency_key", name="uq_notification_intents_key"),
    )
    op.create_index("ix_notification_intents_available", "notification_intents", ["state", "available_at"])

    op.create_table(
        "notification_deliveries",
        sa.Column("delivery_id", uid, primary_key=True),
        sa.Column("intent_id", uid, nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("provider_subject", sa.String(160), nullable=True),
        sa.Column("provider_message_id", sa.String(160), nullable=True),
        sa.Column("state", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lease_owner", sa.String(160), nullable=True),
        sa.Column("lease_until", timestamp, nullable=True),
        sa.Column("next_attempt_at", timestamp, nullable=True),
        sa.Column("last_error_code", sa.String(96), nullable=True),
        sa.Column("last_error_message", sa.String(500), nullable=True),
        sa.Column("last_attempt_at", timestamp, nullable=True),
        sa.Column("completed_at", timestamp, nullable=True),
        sa.Column("delivery_key", sa.String(240), nullable=False),
        sa.Column("provider_metadata_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["intent_id"], ["notification_intents.intent_id"], ondelete="CASCADE"),
        sa.CheckConstraint("state IN ('pending', 'leased', 'succeeded', 'retryable', 'failed', 'dead-letter', 'manual-review')", name="ck_notification_deliveries_state"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_notification_deliveries_attempts"),
        sa.UniqueConstraint("delivery_key", name="uq_notification_deliveries_key"),
    )
    op.create_index("ix_notification_deliveries_claim", "notification_deliveries", ["state", "next_attempt_at", "lease_until"])

    op.create_table(
        "jobs",
        sa.Column("job_id", uid, primary_key=True),
        sa.Column("kind", sa.String(96), nullable=False),
        sa.Column("state", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("available_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.Column("lease_owner", sa.String(160), nullable=True),
        sa.Column("lease_until", timestamp, nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=True),
        sa.Column("idempotency_key", sa.String(240), nullable=False),
        sa.Column("payload_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("last_error_code", sa.String(96), nullable=True),
        sa.Column("last_error_message", sa.String(500), nullable=True),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("state IN ('pending', 'leased', 'succeeded', 'retryable', 'failed', 'dead-letter', 'manual-review')", name="ck_jobs_state"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_jobs_attempts"),
        sa.UniqueConstraint("kind", "idempotency_key", name="uq_jobs_key"),
    )
    op.create_index("ix_jobs_claim", "jobs", ["state", "available_at", "lease_until"])

    op.create_table(
        "outbox_events",
        sa.Column("outbox_event_id", uid, primary_key=True),
        sa.Column("aggregate_id", uid, nullable=False),
        sa.Column("event_kind", sa.String(96), nullable=False),
        sa.Column("state", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("payload_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("idempotency_key", sa.String(240), nullable=False),
        sa.Column("available_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", timestamp, nullable=True),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("state IN ('pending', 'processed', 'failed')", name="ck_outbox_events_state"),
        sa.UniqueConstraint("aggregate_id", "event_kind", "idempotency_key", name="uq_outbox_events_key"),
    )
    op.create_index("ix_outbox_events_available", "outbox_events", ["state", "available_at"])


def downgrade() -> None:
    op.drop_index("ix_outbox_events_available", table_name="outbox_events")
    op.drop_table("outbox_events")
    op.drop_index("ix_jobs_claim", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("ix_notification_deliveries_claim", table_name="notification_deliveries")
    op.drop_table("notification_deliveries")
    op.drop_index("ix_notification_intents_available", table_name="notification_intents")
    op.drop_table("notification_intents")
    op.drop_index("ix_notification_preferences_subject", table_name="notification_preferences")
    op.drop_table("notification_preferences")
