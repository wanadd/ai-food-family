"""Canonical V2 Events domain for temporary food-planning scopes."""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260927_0019"
down_revision: str | None = "20260927_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    uid = postgresql.UUID(as_uuid=False)
    js = postgresql.JSONB()
    timestamp = sa.DateTime(timezone=True)

    op.create_table(
        "events_v2",
        sa.Column("event_id", uid, primary_key=True),
        sa.Column("organizer_person_id", uid, sa.ForeignKey("core_persons.person_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("household_id", uid, sa.ForeignKey("core_households.household_id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("starts_at", timestamp, nullable=False),
        sa.Column("ends_at", timestamp, nullable=True),
        sa.Column("collaboration_mode", sa.String(40), nullable=False, server_default="ORGANIZER_ONLY"),
        sa.Column("status", sa.String(24), nullable=False, server_default="DRAFT"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("creation_idempotency_key", sa.String(128), nullable=False),
        sa.Column("metadata_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('DRAFT','OPEN','PLANNING','READY','ACTIVE','COMPLETED','CANCELLED')", name="ck_events_v2_status"),
        sa.CheckConstraint("collaboration_mode IN ('ORGANIZER_ONLY','RESTRICTIONS_COLLECTION','COLLABORATIVE_PLANNING')", name="ck_events_v2_collaboration"),
        sa.CheckConstraint("version >= 1", name="ck_events_v2_version"),
        sa.UniqueConstraint("creation_idempotency_key", name="uq_events_v2_creation_idempotency"),
    )
    op.create_index("ix_events_v2_organizer", "events_v2", ["organizer_person_id"])
    op.create_index("ix_events_v2_household", "events_v2", ["household_id"])

    op.create_table(
        "event_invitations_v2",
        sa.Column("invitation_id", uid, primary_key=True),
        sa.Column("event_id", uid, sa.ForeignKey("events_v2.event_id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by_person_id", uid, sa.ForeignKey("core_persons.person_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False),
        sa.Column("token_hint", sa.String(16), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("expires_at", timestamp, nullable=True),
        sa.Column("creation_idempotency_key", sa.String(128), nullable=True),
        sa.Column("response_idempotency_key", sa.String(128), nullable=True),
        sa.Column("responded_at", timestamp, nullable=True),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('PENDING','RESPONDED','REVOKED','EXPIRED')", name="ck_event_invitations_v2_status"),
        sa.UniqueConstraint("token_hash", name="uq_event_invitations_v2_token_hash"),
        sa.UniqueConstraint("creation_idempotency_key", name="uq_event_invitations_v2_creation_idempotency"),
        sa.UniqueConstraint("response_idempotency_key", name="uq_event_invitations_v2_response_idempotency"),
    )
    op.create_index("ix_event_invitations_v2_event", "event_invitations_v2", ["event_id"])

    op.create_table(
        "event_participants_v2",
        sa.Column("participant_id", uid, primary_key=True),
        sa.Column("event_id", uid, sa.ForeignKey("events_v2.event_id", ondelete="CASCADE"), nullable=False),
        sa.Column("person_id", uid, sa.ForeignKey("core_persons.person_id", ondelete="SET NULL"), nullable=True),
        sa.Column("invitation_id", uid, sa.ForeignKey("event_invitations_v2.invitation_id", ondelete="SET NULL"), nullable=True),
        sa.Column("participant_kind", sa.String(24), nullable=False),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("age_group", sa.String(16), nullable=False, server_default="UNKNOWN"),
        sa.Column("attendance_status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("created_by_person_id", uid, sa.ForeignKey("core_persons.person_id", ondelete="SET NULL"), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("participant_kind IN ('ORGANIZER','PERSON','GUEST','DEPENDENT')", name="ck_event_participants_v2_kind"),
        sa.CheckConstraint("age_group IN ('ADULT','CHILD','UNKNOWN')", name="ck_event_participants_v2_age"),
        sa.CheckConstraint("attendance_status IN ('PENDING','ACCEPTED','DECLINED')", name="ck_event_participants_v2_attendance"),
        sa.UniqueConstraint("event_id", "person_id", name="uq_event_participants_v2_event_person"),
    )
    op.create_index("ix_event_participants_v2_event", "event_participants_v2", ["event_id"])
    op.create_index("ix_event_participants_v2_person", "event_participants_v2", ["person_id"])

    op.create_table(
        "event_participant_food_facts_v2",
        sa.Column("fact_id", uid, primary_key=True),
        sa.Column("participant_id", uid, sa.ForeignKey("event_participants_v2.participant_id", ondelete="CASCADE"), nullable=False),
        sa.Column("knowledge_state", sa.String(24), nullable=False, server_default="NOT_PROVIDED"),
        sa.Column("restrictions_json", js, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("source_kind", sa.String(32), nullable=False, server_default="MANUAL"),
        sa.Column("provenance_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("knowledge_state IN ('NOT_PROVIDED','UNKNOWN','KNOWN_NONE','KNOWN_PRESENT')", name="ck_event_food_facts_v2_state"),
        sa.CheckConstraint("source_kind IN ('EVENT_RSVP','CORE_PERSON_PROFILE','MANUAL')", name="ck_event_food_facts_v2_source"),
        sa.UniqueConstraint("participant_id", name="uq_event_food_facts_v2_participant"),
        sa.UniqueConstraint("idempotency_key", name="uq_event_food_facts_v2_idempotency"),
    )

    op.create_table(
        "event_menu_revisions_v2",
        sa.Column("revision_id", uid, primary_key=True),
        sa.Column("event_id", uid, sa.ForeignKey("events_v2.event_id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("lifecycle_status", sa.String(24), nullable=False, server_default="DRAFT"),
        sa.Column("expected_event_version", sa.Integer(), nullable=False),
        sa.Column("created_by_person_id", uid, sa.ForeignKey("core_persons.person_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("provenance_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("event_id", "revision_number", name="uq_event_menu_revisions_v2_number"),
        sa.UniqueConstraint("idempotency_key", name="uq_event_menu_revisions_v2_idempotency"),
    )
    op.create_table(
        "event_menu_items_v2",
        sa.Column("menu_item_id", uid, primary_key=True),
        sa.Column("revision_id", uid, sa.ForeignKey("event_menu_revisions_v2.revision_id", ondelete="CASCADE"), nullable=False),
        sa.Column("slot_key", sa.String(96), nullable=False),
        sa.Column("state", sa.String(16), nullable=False, server_default="EMPTY"),
        sa.Column("recipe_version_id", uid, sa.ForeignKey("recipe_versions.recipe_version_id", ondelete="RESTRICT"), nullable=True),
        sa.Column("servings", sa.Float(), nullable=True),
        sa.Column("safety_state", sa.String(24), nullable=False, server_default="UNKNOWN"),
        sa.Column("coverage_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("provenance_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.UniqueConstraint("revision_id", "slot_key", name="uq_event_menu_items_v2_slot"),
    )
    op.create_table(
        "event_menu_item_participants_v2",
        sa.Column("menu_item_id", uid, sa.ForeignKey("event_menu_items_v2.menu_item_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("participant_id", uid, sa.ForeignKey("event_participants_v2.participant_id", ondelete="CASCADE"), primary_key=True),
        sa.UniqueConstraint("menu_item_id", "participant_id", name="uq_event_menu_item_participant_v2"),
    )
    op.create_table(
        "event_shopping_demands_v2",
        sa.Column("demand_id", uid, primary_key=True),
        sa.Column("event_id", uid, sa.ForeignKey("events_v2.event_id", ondelete="CASCADE"), nullable=False),
        sa.Column("menu_item_id", uid, sa.ForeignKey("event_menu_items_v2.menu_item_id", ondelete="SET NULL"), nullable=True),
        sa.Column("display_text", sa.String(300), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(32), nullable=True),
        sa.Column("uncertainty", sa.String(16), nullable=False, server_default="UNKNOWN"),
        sa.Column("state", sa.String(16), nullable=False, server_default="NEEDED"),
        sa.Column("source_kind", sa.String(48), nullable=False, server_default="EVENT_MENU"),
        sa.Column("source_key", sa.String(160), nullable=False),
        sa.Column("shopping_list_id", uid, sa.ForeignKey("shopping_lists.shopping_list_id", ondelete="SET NULL"), nullable=True),
        sa.Column("provenance_json", js, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("uncertainty IN ('UNKNOWN','KNOWN')", name="ck_event_shopping_demands_v2_uncertainty"),
        sa.CheckConstraint("state IN ('NEEDED','CHECKED','PURCHASED')", name="ck_event_shopping_demands_v2_state"),
        sa.UniqueConstraint("event_id", "source_key", name="uq_event_shopping_demands_v2_source"),
    )
    op.create_index("ix_event_shopping_demands_v2_event", "event_shopping_demands_v2", ["event_id"])


def downgrade() -> None:
    op.drop_table("event_shopping_demands_v2")
    op.drop_table("event_menu_item_participants_v2")
    op.drop_table("event_menu_items_v2")
    op.drop_table("event_menu_revisions_v2")
    op.drop_table("event_participant_food_facts_v2")
    op.drop_index("ix_event_participants_v2_person", table_name="event_participants_v2")
    op.drop_index("ix_event_participants_v2_event", table_name="event_participants_v2")
    op.drop_table("event_participants_v2")
    op.drop_index("ix_event_invitations_v2_event", table_name="event_invitations_v2")
    op.drop_table("event_invitations_v2")
    op.drop_index("ix_events_v2_household", table_name="events_v2")
    op.drop_index("ix_events_v2_organizer", table_name="events_v2")
    op.drop_table("events_v2")
