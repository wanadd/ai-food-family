"""food evidence foundation

Revision ID: 20260922_0004
Revises: 20260922_0003
Create Date: 2026-09-22
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260922_0004"
down_revision: str | None = "20260922_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evidence_sources",
        sa.Column("source_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("source_code", sa.String(length=96), nullable=False),
        sa.Column("authority_tier", sa.String(length=32), nullable=False),
        sa.Column("publisher", sa.String(length=200), nullable=True),
        sa.Column("jurisdiction", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="ACTIVE"),
        sa.Column("provenance_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "authority_tier IN ('REGULATORY', 'AUTHORITATIVE_DATASET', 'PRODUCT_LABEL', 'CLINICAL_GUIDANCE', 'INTERNAL_LEGACY', 'AI_PROPOSAL')",
            name="ck_evidence_sources_authority_tier",
        ),
        sa.CheckConstraint("status IN ('ACTIVE', 'RETIRED', 'REVIEW_REQUIRED')", name="ck_evidence_sources_status"),
        sa.UniqueConstraint("source_code", name="uq_evidence_sources_code"),
    )

    op.create_table(
        "source_snapshots",
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("source_version", sa.String(length=128), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("storage_ref", sa.String(length=512), nullable=True),
        sa.Column("release_metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("source_version <> ''", name="ck_source_snapshots_version_not_blank"),
        sa.ForeignKeyConstraint(["source_id"], ["evidence_sources.source_id"], name="fk_source_snapshots_source", ondelete="CASCADE"),
        sa.UniqueConstraint("source_id", "source_version", "content_hash", name="uq_source_snapshots_release_hash"),
    )

    op.create_table(
        "evidence_records",
        sa.Column("record_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("source_record_locator", sa.String(length=512), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('ACTIVE', 'SUPERSEDED', 'REJECTED')", name="ck_evidence_records_status"),
        sa.ForeignKeyConstraint(["snapshot_id"], ["source_snapshots.snapshot_id"], name="fk_evidence_records_snapshot", ondelete="CASCADE"),
        sa.UniqueConstraint("snapshot_id", "source_record_locator", name="uq_evidence_records_snapshot_locator"),
    )

    op.create_table(
        "evidence_claims",
        sa.Column("claim_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("record_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("claim_type", sa.String(length=64), nullable=False),
        sa.Column("subject_type", sa.String(length=64), nullable=False),
        sa.Column("subject_key", sa.String(length=160), nullable=False),
        sa.Column("predicate", sa.String(length=96), nullable=False),
        sa.Column("object_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("confidence", sa.String(length=24), nullable=False, server_default="UNKNOWN"),
        sa.Column("review_status", sa.String(length=32), nullable=False, server_default="NEEDS_REVIEW"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidence IN ('UNKNOWN', 'LOW', 'MEDIUM', 'HIGH', 'SOURCE_BACKED')", name="ck_evidence_claims_confidence"),
        sa.CheckConstraint(
            "review_status IN ('NEEDS_REVIEW', 'REVIEWED_ACCEPTED', 'REVIEWED_REJECTED', 'SUPERSEDED')",
            name="ck_evidence_claims_review_status",
        ),
        sa.ForeignKeyConstraint(["record_id"], ["evidence_records.record_id"], name="fk_evidence_claims_record", ondelete="CASCADE"),
        sa.UniqueConstraint("record_id", "claim_type", "subject_type", "subject_key", "predicate", name="uq_evidence_claim_scope"),
    )

    op.create_table(
        "evidence_applicability",
        sa.Column("applicability_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("person_context_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("product_context_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("process_state", sa.String(length=64), nullable=True),
        sa.Column("applies_status", sa.String(length=24), nullable=False, server_default="UNKNOWN"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("applies_status IN ('APPLIES', 'DOES_NOT_APPLY', 'UNKNOWN', 'REVIEW_REQUIRED')", name="ck_evidence_applicability_status"),
        sa.ForeignKeyConstraint(["claim_id"], ["evidence_claims.claim_id"], name="fk_evidence_applicability_claim", ondelete="CASCADE"),
    )

    op.create_table(
        "food_aliases",
        sa.Column("food_alias_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("food_identity_key", sa.String(length=160), nullable=False),
        sa.Column("alias_text", sa.String(length=240), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False, server_default="und"),
        sa.Column("source_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("confidence", sa.String(length=24), nullable=False, server_default="UNKNOWN"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="REVIEW_REQUIRED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('ACTIVE', 'REVIEW_REQUIRED', 'REJECTED')", name="ck_food_aliases_status"),
        sa.ForeignKeyConstraint(["source_id"], ["evidence_sources.source_id"], name="fk_food_aliases_source", ondelete="SET NULL"),
        sa.UniqueConstraint("food_identity_key", "alias_text", "language", name="uq_food_alias_identity_text_language"),
    )

    op.create_table(
        "food_composition_facts",
        sa.Column("composition_fact_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("food_identity_key", sa.String(length=160), nullable=False),
        sa.Column("nutrient_key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=24), nullable=False),
        sa.Column("basis_amount", sa.Float(), nullable=False),
        sa.Column("basis_unit", sa.String(length=24), nullable=False),
        sa.Column("food_state", sa.String(length=64), nullable=False, server_default="unknown"),
        sa.Column("source_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("source_record_locator", sa.String(length=512), nullable=False),
        sa.Column("confidence", sa.String(length=24), nullable=False, server_default="UNKNOWN"),
        sa.Column("review_status", sa.String(length=32), nullable=False, server_default="NEEDS_REVIEW"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provenance_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("value IS NULL OR value >= 0", name="ck_food_composition_facts_non_negative_or_unknown"),
        sa.CheckConstraint("basis_amount > 0", name="ck_food_composition_facts_basis_positive"),
        sa.CheckConstraint("value IS NULL OR source_id IS NOT NULL", name="ck_food_composition_facts_value_requires_source"),
        sa.CheckConstraint("value IS NULL OR snapshot_id IS NOT NULL", name="ck_food_composition_facts_value_requires_snapshot"),
        sa.CheckConstraint("effective_to IS NULL OR effective_to > effective_from", name="ck_food_composition_facts_period"),
        sa.CheckConstraint(
            "review_status IN ('NEEDS_REVIEW', 'REVIEWED_ACCEPTED', 'REVIEWED_REJECTED', 'SUPERSEDED')",
            name="ck_food_composition_facts_review_status",
        ),
        sa.ForeignKeyConstraint(["source_id"], ["evidence_sources.source_id"], name="fk_food_composition_facts_source", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["snapshot_id"], ["source_snapshots.snapshot_id"], name="fk_food_composition_facts_snapshot", ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "food_identity_key",
            "nutrient_key",
            "food_state",
            "basis_amount",
            "basis_unit",
            "snapshot_id",
            "source_record_locator",
            name="uq_food_composition_fact_source_scope",
        ),
    )
    op.create_index("ix_food_composition_identity_nutrient", "food_composition_facts", ["food_identity_key", "nutrient_key", "food_state"])

    op.create_table(
        "food_evidence_fact_links",
        sa.Column("link_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("fact_table", sa.String(length=80), nullable=False),
        sa.Column("fact_id_text", sa.String(length=120), nullable=False),
        sa.Column("link_type", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("link_type IN ('SUPPORTS', 'CONFLICTS_WITH', 'SUPERSEDES')", name="ck_food_evidence_fact_links_type"),
        sa.ForeignKeyConstraint(["claim_id"], ["evidence_claims.claim_id"], name="fk_food_evidence_fact_links_claim", ondelete="CASCADE"),
        sa.UniqueConstraint("claim_id", "fact_table", "fact_id_text", name="uq_food_evidence_fact_link"),
    )

    op.create_table(
        "product_label_facts",
        sa.Column("product_label_fact_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("product_key", sa.String(length=160), nullable=False),
        sa.Column("fact_type", sa.String(length=64), nullable=False),
        sa.Column("fact_key", sa.String(length=160), nullable=False),
        sa.Column("knowledge_state", sa.String(length=24), nullable=False),
        sa.Column("value_json", postgresql.JSONB(), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("source_record_locator", sa.String(length=512), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False, server_default="NEEDS_REVIEW"),
        sa.Column("provenance_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("knowledge_state IN ('UNKNOWN', 'NOT_PROVIDED', 'KNOWN_NONE', 'KNOWN_PRESENT')", name="ck_product_label_facts_knowledge_state"),
        sa.CheckConstraint(
            "review_status IN ('NEEDS_REVIEW', 'REVIEWED_ACCEPTED', 'REVIEWED_REJECTED', 'SUPERSEDED')",
            name="ck_product_label_facts_review_status",
        ),
        sa.ForeignKeyConstraint(["source_id"], ["evidence_sources.source_id"], name="fk_product_label_facts_source", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["snapshot_id"], ["source_snapshots.snapshot_id"], name="fk_product_label_facts_snapshot", ondelete="RESTRICT"),
        sa.UniqueConstraint("product_key", "fact_type", "fact_key", "snapshot_id", "source_record_locator", name="uq_product_label_fact_source_scope"),
    )
    op.create_index("ix_product_label_facts_product_type", "product_label_facts", ["product_key", "fact_type", "fact_key"])


def downgrade() -> None:
    op.drop_index("ix_product_label_facts_product_type", table_name="product_label_facts")
    op.drop_table("product_label_facts")
    op.drop_table("food_evidence_fact_links")
    op.drop_index("ix_food_composition_identity_nutrient", table_name="food_composition_facts")
    op.drop_table("food_composition_facts")
    op.drop_table("food_aliases")
    op.drop_table("evidence_applicability")
    op.drop_table("evidence_claims")
    op.drop_table("evidence_records")
    op.drop_table("source_snapshots")
    op.drop_table("evidence_sources")
