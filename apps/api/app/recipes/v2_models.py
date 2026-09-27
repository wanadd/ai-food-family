from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.core.models import CoreJSON, CoreUUID


class CanonicalRecipe(Base):
    __tablename__ = "recipes_v2"

    recipe_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="DRAFT")
    canonical_key: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CanonicalRecipeVersion(Base):
    __tablename__ = "recipe_versions"

    recipe_version_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    recipe_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("recipes_v2.recipe_id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    lifecycle_status: Mapped[str] = mapped_column(String(24), nullable=False, default="DRAFT")
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    servings: Mapped[float | None] = mapped_column(Float, nullable=True)
    yield_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    yield_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    safety_claims_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    nutrition_projection_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    gold_v3_validation_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    gold_v3_payload_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    source_provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    originality_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    publication_reason: Mapped[str | None] = mapped_column(String(160), nullable=True)
    last_idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CanonicalRecipeIngredient(Base):
    __tablename__ = "recipe_ingredients_v2"

    ingredient_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    recipe_version_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("recipe_versions.recipe_version_id"), nullable=False)
    food_identity_key: Mapped[str | None] = mapped_column(String(160), nullable=True)
    display_text: Mapped[str] = mapped_column(String(300), nullable=False)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    preparation_expectation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    product_requirement_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shopping_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    normalized_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    normalized_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    quantity_mode: Mapped[str] = mapped_column(String(24), nullable=False, default="UNKNOWN")
    optional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    process_state: Mapped[str | None] = mapped_column(String(48), nullable=True)
    mapping_status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    mapping_provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)


class CanonicalRecipeStep(Base):
    __tablename__ = "recipe_steps_v2"

    step_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    recipe_version_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("recipe_versions.recipe_version_id"), nullable=False)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    expected_process_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)


class CanonicalRecipeFavorite(Base):
    __tablename__ = "recipe_favorites_v2"
    __table_args__ = (UniqueConstraint("account_id", "recipe_id", name="uq_recipe_favorite_v2_account_recipe"),)

    favorite_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    account_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("core_accounts.account_id"), nullable=False)
    recipe_id: Mapped[str] = mapped_column(CoreUUID, ForeignKey("recipes_v2.recipe_id"), nullable=False)
    version_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("recipe_versions.recipe_version_id"), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CanonicalLegacyMapping(Base):
    __tablename__ = "recipe_legacy_mappings"

    mapping_id: Mapped[str] = mapped_column(CoreUUID, primary_key=True)
    legacy_recipe_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    canonical_recipe_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("recipes_v2.recipe_id"), nullable=True)
    canonical_version_id: Mapped[str | None] = mapped_column(CoreUUID, ForeignKey("recipe_versions.recipe_version_id"), nullable=True)
    mapping_status: Mapped[str] = mapped_column(String(24), nullable=False)
    mapping_reason: Mapped[str] = mapped_column(String(160), nullable=False)
    provenance_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False, default=dict)


class CanonicalArchiveFallback(Base):
    __tablename__ = "recipe_archive_fallbacks"

    legacy_recipe_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    archive_payload_json: Mapped[dict] = mapped_column(CoreJSON, nullable=False)
    archived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source_kind: Mapped[str] = mapped_column(String(48), nullable=False, default="LEGACY_ARCHIVE")
