from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.database import Base

CoreUUID = String(36).with_variant(PG_UUID(as_uuid=False), "postgresql")
CoreJSON = JSON().with_variant(JSONB, "postgresql")


class CoreAccount(Base):
    __tablename__ = "core_accounts"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'disabled', 'deleted')", name="ck_core_accounts_status"),
    )

    account_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    primary_person_id: Mapped[str | None] = mapped_column(
        CoreUUID,
        ForeignKey("core_persons.person_id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class CorePerson(Base):
    __tablename__ = "core_persons"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'disabled', 'deleted')", name="ck_core_persons_status"),
        CheckConstraint(
            "birth_date_precision IN ('unknown', 'exact', 'year_month', 'year', 'declared_age_only')",
            name="ck_core_persons_birth_date_precision",
        ),
    )

    person_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    display_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    birth_date_precision: Mapped[str] = mapped_column(String(24), nullable=False, default="unknown")
    birth_date_provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    birth_date_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class CoreAuthIdentity(Base):
    __tablename__ = "core_auth_identities"
    __table_args__ = (
        UniqueConstraint("provider", "provider_subject", name="uq_core_auth_identity_provider_subject"),
        CheckConstraint("provider <> ''", name="ck_core_auth_identities_provider_not_blank"),
        CheckConstraint("provider_subject <> ''", name="ck_core_auth_identities_subject_not_blank"),
        Index("ix_core_auth_identities_account", "account_id"),
    )

    auth_identity_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    account_id: Mapped[str] = mapped_column(
        CoreUUID,
        ForeignKey("core_accounts.account_id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_subject: Mapped[str] = mapped_column(String(160), nullable=False)
    provider_payload_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    provider_metadata_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CoreHousehold(Base):
    __tablename__ = "core_households"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'disabled', 'deleted')", name="ck_core_households_status"),
    )

    household_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class CoreMembership(Base):
    __tablename__ = "core_memberships"
    __table_args__ = (
        UniqueConstraint("person_id", "household_id", "active_from", name="uq_core_membership_person_household_from"),
        CheckConstraint(
            "membership_status IN ('active', 'inactive', 'revoked')",
            name="ck_core_memberships_status",
        ),
        CheckConstraint("active_to IS NULL OR active_to > active_from", name="ck_core_memberships_period"),
        Index("ix_core_memberships_person_status", "person_id", "membership_status"),
        Index("ix_core_memberships_household_status", "household_id", "membership_status"),
    )

    membership_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    person_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="CASCADE"))
    household_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_households.household_id", ondelete="CASCADE"))
    membership_status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    role_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    active_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    active_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ui_default_rank: Mapped[int | None] = mapped_column(nullable=True)
    created_by_account_id: Mapped[str | None] = mapped_column(
        CoreUUID,
        ForeignKey("core_accounts.account_id", ondelete="SET NULL"),
        nullable=True,
    )
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class CorePersonRelationship(Base):
    __tablename__ = "core_person_relationships"
    __table_args__ = (
        UniqueConstraint(
            "subject_person_id",
            "target_person_id",
            "relationship_type",
            "effective_from",
            name="uq_core_person_relationship_scope",
        ),
        CheckConstraint("subject_person_id <> target_person_id", name="ck_core_person_relationship_no_self"),
        CheckConstraint("effective_to IS NULL OR effective_to > effective_from", name="ck_core_person_relationship_period"),
        Index("ix_core_person_relationship_subject", "subject_person_id", "relationship_type"),
        Index("ix_core_person_relationship_target", "target_person_id", "relationship_type"),
    )

    relationship_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    subject_person_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="CASCADE"))
    target_person_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="CASCADE"))
    relationship_type: Mapped[str] = mapped_column(String(48), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CorePermissionGrant(Base):
    __tablename__ = "core_permission_grants"
    __table_args__ = (
        CheckConstraint(
            "grant_status IN ('active', 'revoked', 'expired')",
            name="ck_core_permission_grants_status",
        ),
        CheckConstraint(
            "target_person_id IS NOT NULL OR household_id IS NOT NULL",
            name="ck_core_permission_grants_scope_present",
        ),
        CheckConstraint("effective_to IS NULL OR effective_to > effective_from", name="ck_core_permission_grants_period"),
        Index(
            "ix_core_permission_grants_subject_scope",
            "subject_person_id",
            "domain_scope",
            "capability",
            "grant_status",
        ),
    )

    permission_grant_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    subject_person_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_persons.person_id", ondelete="CASCADE"))
    target_person_id: Mapped[str | None] = mapped_column(
        CoreUUID,
        ForeignKey("core_persons.person_id", ondelete="CASCADE"),
        nullable=True,
    )
    household_id: Mapped[str | None] = mapped_column(
        CoreUUID,
        ForeignKey("core_households.household_id", ondelete="CASCADE"),
        nullable=True,
    )
    domain_scope: Mapped[str] = mapped_column(String(64), nullable=False)
    capability: Mapped[str] = mapped_column(String(96), nullable=False)
    grant_status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LegacyIdMapping(Base):
    __tablename__ = "legacy_id_mappings"
    __table_args__ = (
        UniqueConstraint("legacy_table", "legacy_id_text", "target_table", name="uq_legacy_id_mapping_source_target"),
        Index("ix_legacy_id_mappings_target", "target_table", "target_id_uuid"),
    )

    mapping_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    legacy_table: Mapped[str] = mapped_column(String(80), nullable=False)
    legacy_id_text: Mapped[str] = mapped_column(String(120), nullable=False)
    target_table: Mapped[str] = mapped_column(String(80), nullable=False)
    target_id_uuid: Mapped[str] = mapped_column(CoreUUID, nullable=False)
    confidence: Mapped[str] = mapped_column(String(32), nullable=False, default="source_backed")
    migration_status: Mapped[str] = mapped_column(String(40), nullable=False, default="auto_migrated_with_provenance")
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ExternalIdentity(Base):
    """Provider identity owned by PLANAM, not a provider-specific business row."""

    __tablename__ = "external_identities"
    __table_args__ = (
        UniqueConstraint("provider", "provider_subject", name="uq_external_identity_provider_subject"),
        CheckConstraint("provider <> ''", name="ck_external_identities_provider_not_blank"),
        CheckConstraint("provider_subject <> ''", name="ck_external_identities_subject_not_blank"),
        CheckConstraint(
            "status IN ('active', 'revoked')",
            name="ck_external_identities_status",
        ),
        Index("ix_external_identities_account", "account_id"),
    )

    identity_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    account_id: Mapped[str] = mapped_column(
        CoreUUID,
        ForeignKey("core_accounts.account_id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_subject: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    provider_payload_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    provider_metadata_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class VerifiedContact(Base):
    __tablename__ = "verified_contacts"
    __table_args__ = (
        UniqueConstraint("account_id", "contact_kind", "value_hash", name="uq_verified_contact_account_value"),
        CheckConstraint("contact_kind IN ('phone', 'email')", name="ck_verified_contacts_kind"),
        Index("ix_verified_contacts_value", "contact_kind", "value_hash"),
    )

    contact_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    account_id: Mapped[str] = mapped_column(
        CoreUUID,
        ForeignKey("core_accounts.account_id", ondelete="CASCADE"),
        nullable=False,
    )
    contact_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    value_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    masked_value: Mapped[str | None] = mapped_column(String(160), nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CoreSession(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint("client_type <> ''", name="ck_sessions_client_type_not_blank"),
        CheckConstraint("expires_at > issued_at", name="ck_sessions_expiry"),
        Index("ix_sessions_account_status", "account_id", "revoked_at", "expires_at"),
    )

    session_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    account_id: Mapped[str] = mapped_column(
        CoreUUID,
        ForeignKey("core_accounts.account_id", ondelete="CASCADE"),
        nullable=False,
    )
    client_type: Mapped[str] = mapped_column(String(24), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    refresh_token_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rotation_counter: Mapped[int] = mapped_column(nullable=False, default=0)
    security_metadata_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)


class IdentityLinkIntent(Base):
    __tablename__ = "identity_link_intents"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'consumed', 'expired', 'cancelled')", name="ck_identity_link_intents_status"),
        CheckConstraint("expires_at > created_at", name="ck_identity_link_intents_expiry"),
        Index("ix_identity_link_intents_account_status", "initiating_account_id", "status"),
    )

    intent_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    initiating_account_id: Mapped[str] = mapped_column(
        CoreUUID,
        ForeignKey("core_accounts.account_id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    secret_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
