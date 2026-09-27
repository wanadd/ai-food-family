"""Wave 2 canonical evidence links and deterministic safety decisions."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260927_0013"
down_revision: str | None = "20260927_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = lambda: postgresql.UUID(as_uuid=False)
JSON = lambda: postgresql.JSONB()


def upgrade() -> None:
    op.create_table(
        "source_registry",
        sa.Column("source_registry_id", UUID(), primary_key=True),
        sa.Column("source_code", sa.String(96), nullable=False),
        sa.Column("authority_tier", sa.String(32), nullable=False),
        sa.Column("jurisdiction", sa.String(80), nullable=True),
        sa.Column("publisher", sa.String(200), nullable=True),
        sa.Column("publication_version", sa.String(128), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="ACTIVE"),
        sa.Column("metadata_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("source_code", name="uq_source_registry_code"),
        sa.CheckConstraint("authority_tier IN ('REGULATORY', 'AUTHORITATIVE_DATASET', 'PRODUCT_LABEL', 'CLINICAL_GUIDANCE', 'PLANAM_POLICY', 'INTERNAL_LEGACY', 'AI_PROPOSAL')", name="ck_source_registry_tier"),
        sa.CheckConstraint("status IN ('ACTIVE', 'RETIRED', 'REVIEW_REQUIRED')", name="ck_source_registry_status"),
    )
    op.add_column("source_snapshots", sa.Column("source_registry_id", UUID(), nullable=True))
    op.create_foreign_key("fk_source_snapshots_registry", "source_snapshots", "source_registry", ["source_registry_id"], ["source_registry_id"], ondelete="SET NULL")
    op.create_table(
        "food_evidence_links",
        sa.Column("food_evidence_link_id", UUID(), primary_key=True),
        sa.Column("food_identity_id", sa.Integer(), nullable=False),
        sa.Column("claim_id", UUID(), nullable=False),
        sa.Column("relation_type", sa.String(24), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["claim_id"], ["evidence_claims.claim_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("food_identity_id", "claim_id", "relation_type", name="uq_food_evidence_link"),
        sa.CheckConstraint("relation_type IN ('SUPPORTS', 'CONFLICTS_WITH', 'SUPERSEDES')", name="ck_food_evidence_links_relation"),
        sa.CheckConstraint("status IN ('ACTIVE', 'SUPERSEDED')", name="ck_food_evidence_links_status"),
    )
    op.create_table(
        "safety_rules",
        sa.Column("safety_rule_id", UUID(), primary_key=True),
        sa.Column("rule_key", sa.String(160), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="DRAFT"),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("target_concept", sa.String(160), nullable=False),
        sa.Column("facts_consumed_json", JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("evidence_claim_ids_json", JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("explanation_code", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("rule_key", "version", name="uq_safety_rules_key_version"),
        sa.CheckConstraint("version > 0", name="ck_safety_rules_version_positive"),
        sa.CheckConstraint("status IN ('DRAFT', 'PUBLISHED', 'RETIRED')", name="ck_safety_rules_status"),
        sa.CheckConstraint("decision IN ('BLOCK', 'ESCALATE', 'UNKNOWN', 'WARN', 'SAFE')", name="ck_safety_rules_decision"),
        sa.CheckConstraint("effective_to IS NULL OR effective_to > effective_from", name="ck_safety_rules_period"),
    )
    op.create_table(
        "safety_decisions",
        sa.Column("safety_decision_id", UUID(), primary_key=True),
        sa.Column("person_id", UUID(), nullable=False),
        sa.Column("food_identity_id", sa.Integer(), nullable=True),
        sa.Column("packaged_product_id", sa.Integer(), nullable=True),
        sa.Column("process_state", sa.String(64), nullable=True),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("reason_codes_json", JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("safety_rule_id", UUID(), nullable=True),
        sa.Column("evidence_claim_ids_json", JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("request_fingerprint", sa.String(128), nullable=True),
        sa.ForeignKeyConstraint(["person_id"], ["core_persons.person_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["safety_rule_id"], ["safety_rules.safety_rule_id"], ondelete="SET NULL"),
        sa.UniqueConstraint("person_id", "idempotency_key", name="uq_safety_decisions_person_idempotency"),
        sa.CheckConstraint("decision IN ('BLOCK', 'ESCALATE', 'UNKNOWN', 'WARN', 'SAFE')", name="ck_safety_decisions_decision"),
    )
    op.create_index("ix_safety_decisions_person_time", "safety_decisions", ["person_id", "evaluated_at"])
    # The three identity tables are legacy custom-SQL-owned at this checkpoint.
    # Add relational protection when they exist, while keeping a fresh Alembic
    # rehearsal independent from the legacy startup bootstrap.
    op.execute("""
    DO $$
    BEGIN
        IF to_regclass('food_identities') IS NOT NULL AND NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'food_evidence_links_food_identity_fkey') THEN
            ALTER TABLE food_evidence_links ADD CONSTRAINT food_evidence_links_food_identity_fkey FOREIGN KEY (food_identity_id) REFERENCES food_identities(id) ON DELETE CASCADE;
        END IF;
        IF to_regclass('food_identities') IS NOT NULL AND NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'safety_decisions_food_identity_fkey') THEN
            ALTER TABLE safety_decisions ADD CONSTRAINT safety_decisions_food_identity_fkey FOREIGN KEY (food_identity_id) REFERENCES food_identities(id) ON DELETE SET NULL;
        END IF;
        IF to_regclass('packaged_products') IS NOT NULL AND NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'safety_decisions_packaged_product_fkey') THEN
            ALTER TABLE safety_decisions ADD CONSTRAINT safety_decisions_packaged_product_fkey FOREIGN KEY (packaged_product_id) REFERENCES packaged_products(id) ON DELETE SET NULL;
        END IF;
    END $$;
    """)
    op.drop_constraint("ck_food_profile_facts_knowledge_state", "food_profile_facts", type_="check")
    op.create_check_constraint("ck_food_profile_facts_knowledge_state", "food_profile_facts", "knowledge_state IN ('UNKNOWN', 'NOT_PROVIDED', 'KNOWN_NONE', 'KNOWN_PRESENT', 'DECLINED', 'NOT_APPLICABLE')")


def downgrade() -> None:
    op.drop_constraint("fk_source_snapshots_registry", "source_snapshots", type_="foreignkey")
    op.drop_column("source_snapshots", "source_registry_id")
    op.drop_constraint("ck_food_profile_facts_knowledge_state", "food_profile_facts", type_="check")
    op.create_check_constraint("ck_food_profile_facts_knowledge_state", "food_profile_facts", "knowledge_state IN ('UNKNOWN', 'NOT_PROVIDED', 'KNOWN_NONE', 'KNOWN_PRESENT')")
    op.drop_index("ix_safety_decisions_person_time", table_name="safety_decisions")
    op.drop_table("safety_decisions")
    op.drop_table("safety_rules")
    op.drop_table("food_evidence_links")
    op.drop_table("source_registry")
