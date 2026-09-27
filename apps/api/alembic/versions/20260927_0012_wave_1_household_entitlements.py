"""Wave 1 household idempotency and entitlement persistence."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260927_0012"
down_revision: str | None = "20260927_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = lambda: postgresql.UUID(as_uuid=False)
JSON = lambda: postgresql.JSONB()


def upgrade() -> None:
    op.add_column("core_persons", sa.Column("last_mutation_idempotency_key", sa.String(128), nullable=True))
    op.create_unique_constraint("uq_core_persons_last_mutation_idempotency", "core_persons", ["last_mutation_idempotency_key"])
    op.add_column("core_households", sa.Column("created_by_account_id", UUID(), nullable=True))
    op.add_column("core_households", sa.Column("creation_idempotency_key", sa.String(128), nullable=True))
    op.create_foreign_key("fk_core_households_created_by_account", "core_households", "core_accounts", ["created_by_account_id"], ["account_id"], ondelete="SET NULL")
    op.create_unique_constraint("uq_core_households_creation_idempotency", "core_households", ["creation_idempotency_key"])
    op.add_column("core_memberships", sa.Column("idempotency_key", sa.String(128), nullable=True))
    op.create_unique_constraint("uq_core_memberships_idempotency", "core_memberships", ["idempotency_key"])

    op.create_table(
        "entitlement_plans",
        sa.Column("plan_id", UUID(), primary_key=True),
        sa.Column("plan_key", sa.String(96), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="active"),
        sa.Column("policy_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("plan_key", "version", name="uq_entitlement_plan_key_version"),
        sa.CheckConstraint("status IN ('active', 'inactive', 'archived')", name="ck_entitlement_plans_status"),
        sa.CheckConstraint("version > 0", name="ck_entitlement_plans_version_positive"),
    )
    op.create_table(
        "entitlement_grants",
        sa.Column("grant_id", UUID(), primary_key=True),
        sa.Column("account_id", UUID(), nullable=True),
        sa.Column("household_id", UUID(), nullable=True),
        sa.Column("person_id", UUID(), nullable=True),
        sa.Column("capability", sa.String(128), nullable=False),
        sa.Column("limit_value", sa.Integer(), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("grant_status", sa.String(24), nullable=False, server_default="active"),
        sa.Column("source", sa.String(96), nullable=False, server_default="policy"),
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("provenance_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "(account_id IS NOT NULL AND household_id IS NULL AND person_id IS NULL) "
            "OR (account_id IS NULL AND household_id IS NOT NULL AND person_id IS NULL) "
            "OR (account_id IS NULL AND household_id IS NULL AND person_id IS NOT NULL)",
            name="ck_entitlement_grants_one_subject",
        ),
        sa.CheckConstraint("effective_to IS NULL OR effective_to > effective_from", name="ck_entitlement_grants_period"),
        sa.CheckConstraint("grant_status IN ('active', 'revoked', 'expired')", name="ck_entitlement_grants_status"),
        sa.CheckConstraint("limit_value IS NULL OR limit_value >= 0", name="ck_entitlement_grants_limit_nonnegative"),
        sa.ForeignKeyConstraint(["account_id"], ["core_accounts.account_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["core_households.household_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["person_id"], ["core_persons.person_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("idempotency_key", name="uq_entitlement_grants_idempotency"),
    )
    op.create_index("ix_entitlement_grants_subject_capability", "entitlement_grants", ["account_id", "household_id", "person_id", "capability", "grant_status"])
    op.create_table(
        "entitlement_consumptions",
        sa.Column("consumption_id", UUID(), primary_key=True),
        sa.Column("grant_id", UUID(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("provenance_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("amount >= 0", name="ck_entitlement_consumptions_amount_nonnegative"),
        sa.ForeignKeyConstraint(["grant_id"], ["entitlement_grants.grant_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("grant_id", "idempotency_key", name="uq_entitlement_consumptions_grant_idempotency"),
    )
    op.create_index("ix_entitlement_consumptions_grant", "entitlement_consumptions", ["grant_id", "consumed_at"])


def downgrade() -> None:
    op.drop_index("ix_entitlement_consumptions_grant", table_name="entitlement_consumptions")
    op.drop_table("entitlement_consumptions")
    op.drop_index("ix_entitlement_grants_subject_capability", table_name="entitlement_grants")
    op.drop_table("entitlement_grants")
    op.drop_table("entitlement_plans")
    op.drop_constraint("uq_core_memberships_idempotency", "core_memberships", type_="unique")
    op.drop_column("core_memberships", "idempotency_key")
    op.drop_constraint("uq_core_households_creation_idempotency", "core_households", type_="unique")
    op.drop_constraint("fk_core_households_created_by_account", "core_households", type_="foreignkey")
    op.drop_column("core_households", "creation_idempotency_key")
    op.drop_column("core_households", "created_by_account_id")
    op.drop_constraint("uq_core_persons_last_mutation_idempotency", "core_persons", type_="unique")
    op.drop_column("core_persons", "last_mutation_idempotency_key")
