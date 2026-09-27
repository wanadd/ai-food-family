"""Wave 0 client-neutral identity, session and linking foundation."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260927_0011"
down_revision: str | None = "20260924_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = lambda: postgresql.UUID(as_uuid=False)
JSON = lambda: postgresql.JSONB()


def upgrade() -> None:
    op.create_table(
        "external_identities",
        sa.Column("identity_id", UUID(), primary_key=True),
        sa.Column("account_id", UUID(), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("provider_subject", sa.String(160), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="active"),
        sa.Column("provider_payload_hash", sa.String(128), nullable=True),
        sa.Column("provider_metadata_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("provider <> ''", name="ck_external_identities_provider_not_blank"),
        sa.CheckConstraint("provider_subject <> ''", name="ck_external_identities_subject_not_blank"),
        sa.CheckConstraint("status IN ('active', 'revoked')", name="ck_external_identities_status"),
        sa.ForeignKeyConstraint(["account_id"], ["core_accounts.account_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("provider", "provider_subject", name="uq_external_identity_provider_subject"),
    )
    op.create_index("ix_external_identities_account", "external_identities", ["account_id"])

    op.create_table(
        "verified_contacts",
        sa.Column("contact_id", UUID(), primary_key=True),
        sa.Column("account_id", UUID(), nullable=False),
        sa.Column("contact_kind", sa.String(16), nullable=False),
        sa.Column("value_hash", sa.String(128), nullable=False),
        sa.Column("masked_value", sa.String(160), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("contact_kind IN ('phone', 'email')", name="ck_verified_contacts_kind"),
        sa.ForeignKeyConstraint(["account_id"], ["core_accounts.account_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("account_id", "contact_kind", "value_hash", name="uq_verified_contact_account_value"),
    )
    op.create_index("ix_verified_contacts_value", "verified_contacts", ["contact_kind", "value_hash"])

    op.create_table(
        "sessions",
        sa.Column("session_id", UUID(), primary_key=True),
        sa.Column("account_id", UUID(), nullable=False),
        sa.Column("client_type", sa.String(24), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False),
        sa.Column("refresh_token_hash", sa.String(128), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rotation_counter", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("security_metadata_json", JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("client_type <> ''", name="ck_sessions_client_type_not_blank"),
        sa.CheckConstraint("expires_at > issued_at", name="ck_sessions_expiry"),
        sa.ForeignKeyConstraint(["account_id"], ["core_accounts.account_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token_hash", name="uq_sessions_token_hash"),
        sa.UniqueConstraint("refresh_token_hash", name="uq_sessions_refresh_token_hash"),
    )
    op.create_index("ix_sessions_account_status", "sessions", ["account_id", "revoked_at", "expires_at"])

    op.create_table(
        "identity_link_intents",
        sa.Column("intent_id", UUID(), primary_key=True),
        sa.Column("initiating_account_id", UUID(), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("secret_hash", sa.String(128), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('pending', 'consumed', 'expired', 'cancelled')", name="ck_identity_link_intents_status"),
        sa.CheckConstraint("expires_at > created_at", name="ck_identity_link_intents_expiry"),
        sa.ForeignKeyConstraint(["initiating_account_id"], ["core_accounts.account_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("secret_hash", name="uq_identity_link_intents_secret_hash"),
    )
    op.create_index("ix_identity_link_intents_account_status", "identity_link_intents", ["initiating_account_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_identity_link_intents_account_status", table_name="identity_link_intents")
    op.drop_table("identity_link_intents")
    op.drop_index("ix_sessions_account_status", table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("ix_verified_contacts_value", table_name="verified_contacts")
    op.drop_table("verified_contacts")
    op.drop_index("ix_external_identities_account", table_name="external_identities")
    op.drop_table("external_identities")
