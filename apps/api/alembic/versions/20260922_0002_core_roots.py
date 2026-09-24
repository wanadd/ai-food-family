"""core identity roots

Revision ID: 20260922_0002
Revises: 20260922_0001
Create Date: 2026-09-22
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260922_0002"
down_revision: str | None = "20260922_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "core_persons",
        sa.Column("person_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("display_name", sa.String(length=160), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("birth_date_precision", sa.String(length=24), nullable=False, server_default="unknown"),
        sa.Column("birth_date_provenance_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("birth_date_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('active', 'disabled', 'deleted')", name="ck_core_persons_status"),
        sa.CheckConstraint(
            "birth_date_precision IN ('unknown', 'exact', 'year_month', 'year', 'declared_age_only')",
            name="ck_core_persons_birth_date_precision",
        ),
    )

    op.create_table(
        "core_accounts",
        sa.Column("account_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column("primary_person_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('active', 'disabled', 'deleted')", name="ck_core_accounts_status"),
        sa.ForeignKeyConstraint(
            ["primary_person_id"],
            ["core_persons.person_id"],
            name="fk_core_accounts_primary_person",
            ondelete="SET NULL",
            deferrable=True,
            initially="DEFERRED",
        ),
    )

    op.create_table(
        "core_auth_identities",
        sa.Column("auth_identity_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_subject", sa.String(length=160), nullable=False),
        sa.Column("provider_payload_hash", sa.String(length=128), nullable=True),
        sa.Column("provider_metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("provider <> ''", name="ck_core_auth_identities_provider_not_blank"),
        sa.CheckConstraint("provider_subject <> ''", name="ck_core_auth_identities_subject_not_blank"),
        sa.ForeignKeyConstraint(["account_id"], ["core_accounts.account_id"], name="fk_core_auth_identities_account", ondelete="CASCADE"),
    )
    op.create_unique_constraint(
        "uq_core_auth_identity_provider_subject",
        "core_auth_identities",
        ["provider", "provider_subject"],
    )
    op.create_index("ix_core_auth_identities_account", "core_auth_identities", ["account_id"])

    op.create_table(
        "core_households",
        sa.Column("household_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('active', 'disabled', 'deleted')", name="ck_core_households_status"),
    )

    op.create_table(
        "core_memberships",
        sa.Column("membership_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("household_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("membership_status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column("role_label", sa.String(length=64), nullable=True),
        sa.Column("active_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("active_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ui_default_rank", sa.Integer(), nullable=True),
        sa.Column("created_by_account_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("provenance_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("membership_status IN ('active', 'inactive', 'revoked')", name="ck_core_memberships_status"),
        sa.CheckConstraint("active_to IS NULL OR active_to > active_from", name="ck_core_memberships_period"),
        sa.ForeignKeyConstraint(["person_id"], ["core_persons.person_id"], name="fk_core_memberships_person", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], name="fk_core_memberships_household", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_account_id"], ["core_accounts.account_id"], name="fk_core_memberships_created_by_account", ondelete="SET NULL"),
        sa.UniqueConstraint("person_id", "household_id", "active_from", name="uq_core_membership_person_household_from"),
    )
    op.create_index("ix_core_memberships_person_status", "core_memberships", ["person_id", "membership_status"])
    op.create_index("ix_core_memberships_household_status", "core_memberships", ["household_id", "membership_status"])

    op.create_table(
        "core_person_relationships",
        sa.Column("relationship_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("subject_person_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("target_person_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("relationship_type", sa.String(length=48), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provenance_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("subject_person_id <> target_person_id", name="ck_core_person_relationship_no_self"),
        sa.CheckConstraint("effective_to IS NULL OR effective_to > effective_from", name="ck_core_person_relationship_period"),
        sa.ForeignKeyConstraint(["subject_person_id"], ["core_persons.person_id"], name="fk_core_person_relationship_subject", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_person_id"], ["core_persons.person_id"], name="fk_core_person_relationship_target", ondelete="CASCADE"),
        sa.UniqueConstraint(
            "subject_person_id",
            "target_person_id",
            "relationship_type",
            "effective_from",
            name="uq_core_person_relationship_scope",
        ),
    )
    op.create_index("ix_core_person_relationship_subject", "core_person_relationships", ["subject_person_id", "relationship_type"])
    op.create_index("ix_core_person_relationship_target", "core_person_relationships", ["target_person_id", "relationship_type"])

    op.create_table(
        "core_permission_grants",
        sa.Column("permission_grant_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("subject_person_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("target_person_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("household_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("domain_scope", sa.String(length=64), nullable=False),
        sa.Column("capability", sa.String(length=96), nullable=False),
        sa.Column("grant_status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provenance_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("grant_status IN ('active', 'revoked', 'expired')", name="ck_core_permission_grants_status"),
        sa.CheckConstraint("target_person_id IS NOT NULL OR household_id IS NOT NULL", name="ck_core_permission_grants_scope_present"),
        sa.CheckConstraint("effective_to IS NULL OR effective_to > effective_from", name="ck_core_permission_grants_period"),
        sa.ForeignKeyConstraint(["subject_person_id"], ["core_persons.person_id"], name="fk_core_permission_grants_subject", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_person_id"], ["core_persons.person_id"], name="fk_core_permission_grants_target", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], name="fk_core_permission_grants_household", ondelete="CASCADE"),
    )
    op.create_index(
        "ix_core_permission_grants_subject_scope",
        "core_permission_grants",
        ["subject_person_id", "domain_scope", "capability", "grant_status"],
    )

    op.create_table(
        "legacy_id_mappings",
        sa.Column("mapping_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("legacy_table", sa.String(length=80), nullable=False),
        sa.Column("legacy_id_text", sa.String(length=120), nullable=False),
        sa.Column("target_table", sa.String(length=80), nullable=False),
        sa.Column("target_id_uuid", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("confidence", sa.String(length=32), nullable=False, server_default="source_backed"),
        sa.Column("migration_status", sa.String(length=40), nullable=False, server_default="auto_migrated_with_provenance"),
        sa.Column("provenance_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("legacy_table", "legacy_id_text", "target_table", name="uq_legacy_id_mapping_source_target"),
    )
    op.create_index("ix_legacy_id_mappings_target", "legacy_id_mappings", ["target_table", "target_id_uuid"])


def downgrade() -> None:
    op.drop_index("ix_legacy_id_mappings_target", table_name="legacy_id_mappings")
    op.drop_table("legacy_id_mappings")
    op.drop_index("ix_core_permission_grants_subject_scope", table_name="core_permission_grants")
    op.drop_table("core_permission_grants")
    op.drop_index("ix_core_person_relationship_target", table_name="core_person_relationships")
    op.drop_index("ix_core_person_relationship_subject", table_name="core_person_relationships")
    op.drop_table("core_person_relationships")
    op.drop_index("ix_core_memberships_household_status", table_name="core_memberships")
    op.drop_index("ix_core_memberships_person_status", table_name="core_memberships")
    op.drop_table("core_memberships")
    op.drop_table("core_households")
    op.drop_index("ix_core_auth_identities_account", table_name="core_auth_identities")
    op.drop_constraint("uq_core_auth_identity_provider_subject", "core_auth_identities", type_="unique")
    op.drop_table("core_auth_identities")
    op.drop_table("core_accounts")
    op.drop_table("core_persons")
