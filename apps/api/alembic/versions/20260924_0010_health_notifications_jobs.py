"""Health projections, notification intents, entitlements and durable jobs."""
from __future__ import annotations
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260924_0010"
down_revision: str | None = "20260924_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
UUID = lambda: postgresql.UUID(as_uuid=False)
JSON = lambda: postgresql.JSONB()

def upgrade() -> None:
    op.create_table(
        "health_projections_v2",
        sa.Column("projection_id", UUID(), primary_key=True),
        sa.Column("person_id", UUID(), nullable=False),
        sa.Column("projection_date", sa.Date(), nullable=False),
        sa.Column("completeness", sa.String(24), nullable=False),
        sa.Column("planned_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("actual_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("deviation_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("safety_status", sa.String(24), nullable=False, server_default="UNKNOWN"),
        sa.Column("source_refs_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("calculation_version", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["person_id"], ["core_persons.person_id"], ondelete="CASCADE"),
        sa.CheckConstraint("completeness IN ('COMPLETE', 'PARTIAL', 'UNKNOWN')", name="ck_health_projection_completeness"),
        sa.CheckConstraint("safety_status IN ('BLOCK', 'ESCALATE', 'UNKNOWN', 'WARN', 'SAFE')", name="ck_health_projection_safety"),
        sa.UniqueConstraint("person_id", "projection_date", "calculation_version", name="uq_health_projection_version"),
    )
    op.create_table(
        "health_deviations_v2",
        sa.Column("deviation_id", UUID(), primary_key=True),
        sa.Column("projection_id", UUID(), nullable=False),
        sa.Column("deviation_kind", sa.String(48), nullable=False),
        sa.Column("severity", sa.String(24), nullable=False),
        sa.Column("known_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("unknown_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("provenance_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["projection_id"], ["health_projections_v2.projection_id"], ondelete="CASCADE"),
        sa.CheckConstraint("severity IN ('INFO', 'WARN', 'ESCALATE', 'BLOCK', 'UNKNOWN')", name="ck_health_deviation_severity"),
    )
    op.create_table(
        "notification_intents_v2",
        sa.Column("intent_id", UUID(), primary_key=True),
        sa.Column("recipient_person_id", UUID(), nullable=True),
        sa.Column("household_id", UUID(), nullable=True),
        sa.Column("intent_type", sa.String(64), nullable=False),
        sa.Column("payload_ref_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("priority", sa.String(16), nullable=False, server_default="NORMAL"),
        sa.Column("not_before", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_domain", sa.String(48), nullable=False),
        sa.Column("dedupe_key", sa.String(200), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["recipient_person_id"], ["core_persons.person_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.CheckConstraint("priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')", name="ck_notification_intent_priority"),
        sa.CheckConstraint("status IN ('PENDING', 'SCHEDULED', 'DELIVERED', 'CANCELLED', 'FAILED')", name="ck_notification_intent_status"),
        sa.UniqueConstraint("dedupe_key", name="uq_notification_intent_dedupe"),
    )
    op.create_table(
        "notification_deliveries_v2",
        sa.Column("delivery_id", UUID(), primary_key=True),
        sa.Column("intent_id", UUID(), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("preference_status", sa.String(24), nullable=False, server_default="ALLOWED"),
        sa.Column("quiet_hours_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("external_reference", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["intent_id"], ["notification_intents_v2.intent_id"], ondelete="CASCADE"),
        sa.CheckConstraint("channel IN ('TELEGRAM', 'PUSH', 'EMAIL', 'OTHER')", name="ck_notification_delivery_channel"),
        sa.CheckConstraint("preference_status IN ('ALLOWED', 'QUIET_HOURS', 'DISABLED', 'UNKNOWN')", name="ck_notification_preference_status"),
        sa.CheckConstraint("delivery_status IN ('PENDING', 'PROCESSING', 'DELIVERED', 'FAILED', 'DEAD')", name="ck_notification_delivery_status"),
        sa.UniqueConstraint("intent_id", "channel", name="uq_notification_delivery_channel"),
    )
    op.create_table(
        "entitlement_grants_v2",
        sa.Column("grant_id", UUID(), primary_key=True),
        sa.Column("subject_kind", sa.String(24), nullable=False),
        sa.Column("subject_id", UUID(), nullable=False),
        sa.Column("capability", sa.String(128), nullable=False),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("source_kind", sa.String(32), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provenance_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("subject_kind IN ('PERSON', 'HOUSEHOLD', 'ACCOUNT')", name="ck_entitlement_subject_kind"),
        sa.CheckConstraint("capability <> ''", name="ck_entitlement_capability_not_blank"),
        sa.CheckConstraint("decision IN ('ALLOW', 'DENY')", name="ck_entitlement_decision"),
        sa.CheckConstraint("source_kind IN ('SUBSCRIPTION_COMPATIBILITY', 'GRANT', 'POLICY', 'SYSTEM')", name="ck_entitlement_source_kind"),
        sa.CheckConstraint("effective_to IS NULL OR effective_to > effective_from", name="ck_entitlement_period"),
        sa.UniqueConstraint("subject_kind", "subject_id", "capability", "effective_from", name="uq_entitlement_grant_version"),
    )
    op.create_table(
        "entitlement_consumptions_v2",
        sa.Column("consumption_id", UUID(), primary_key=True),
        sa.Column("subject_kind", sa.String(24), nullable=False),
        sa.Column("subject_id", UUID(), nullable=False),
        sa.Column("capability", sa.String(128), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("provenance_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("quantity > 0", name="ck_entitlement_consumption_positive"),
        sa.UniqueConstraint("idempotency_key", name="uq_entitlement_consumption_idempotency"),
    )
    op.create_table(
        "durable_jobs_v2",
        sa.Column("job_id", UUID(), primary_key=True),
        sa.Column("job_type", sa.String(96), nullable=False),
        sa.Column("payload_ref_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("lease_owner", sa.String(160), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(1000), nullable=True),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('PENDING', 'RUNNING', 'RETRY', 'SUCCEEDED', 'FAILED', 'DEAD')", name="ck_durable_job_status"),
        sa.CheckConstraint("attempts >= 0 AND max_attempts > 0", name="ck_durable_job_attempts"),
        sa.UniqueConstraint("idempotency_key", name="uq_durable_job_idempotency"),
    )
    op.create_index("ix_durable_jobs_available", "durable_jobs_v2", ["status", "available_at", "lease_until"])
    op.create_table(
        "outbox_events_v2",
        sa.Column("outbox_event_id", UUID(), primary_key=True),
        sa.Column("event_type", sa.String(96), nullable=False),
        sa.Column("aggregate_type", sa.String(96), nullable=False),
        sa.Column("aggregate_id", sa.String(160), nullable=False),
        sa.Column("payload_ref_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("lease_owner", sa.String(160), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(1000), nullable=True),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('PENDING', 'PROCESSING', 'DELIVERED', 'FAILED', 'DEAD')", name="ck_outbox_status"),
        sa.CheckConstraint("attempts >= 0", name="ck_outbox_attempts"),
        sa.UniqueConstraint("idempotency_key", name="uq_outbox_idempotency"),
    )
    op.create_index("ix_outbox_available", "outbox_events_v2", ["status", "available_at", "lease_until"])

def downgrade() -> None:
    op.drop_index("ix_outbox_available", table_name="outbox_events_v2")
    op.drop_table("outbox_events_v2")
    op.drop_index("ix_durable_jobs_available", table_name="durable_jobs_v2")
    for table in ("durable_jobs_v2", "entitlement_consumptions_v2", "entitlement_grants_v2", "notification_deliveries_v2", "notification_intents_v2", "health_deviations_v2", "health_projections_v2"):
        op.drop_table(table)
