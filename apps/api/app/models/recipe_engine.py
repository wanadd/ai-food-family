"""Recipe Engine v1 — extended storage models.

Tables introduced in Sprint 2 (see ``database_migrations.py``).
Existing ``recipes`` and related tables are unchanged.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RecipeCollection(Base):
    __tablename__ = "recipe_collections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    owner_family_id: Mapped[int | None] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), index=True, nullable=True
    )
    visibility: Mapped[str] = mapped_column(String(16), default="personal", index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(500), default="")
    emoji: Mapped[str | None] = mapped_column(String(8), nullable=True)
    color: Mapped[str | None] = mapped_column(String(16), nullable=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dynamic: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    recipe_links = relationship(
        "CollectionRecipe",
        back_populates="collection",
        cascade="all, delete-orphan",
        order_by="CollectionRecipe.position",
    )


class CollectionRecipe(Base):
    __tablename__ = "collection_recipes"
    __table_args__ = (
        UniqueConstraint(
            "collection_id", "recipe_id", name="uq_collection_recipes_collection_recipe"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    collection_id: Mapped[int] = mapped_column(
        ForeignKey("recipe_collections.id", ondelete="CASCADE"), index=True
    )
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0)
    added_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)

    collection = relationship("RecipeCollection", back_populates="recipe_links")
    recipe = relationship("Recipe")


class RecipeHistory(Base):
    """Append-only cooking history (one row per cooked event)."""

    __tablename__ = "recipe_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    family_id: Mapped[int | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"), index=True, nullable=True
    )
    family_member_id: Mapped[int | None] = mapped_column(
        ForeignKey("family_members.id", ondelete="SET NULL"), index=True, nullable=True
    )
    servings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cooked_on: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    source: Mapped[str] = mapped_column(String(16), default="manual")
    notes: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    recipe = relationship("Recipe")


class FamilyRecipePreference(Base):
    __tablename__ = "family_recipe_preferences"
    __table_args__ = (
        UniqueConstraint(
            "family_member_id",
            "recipe_id",
            name="uq_family_recipe_preferences_member_recipe",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    family_id: Mapped[int] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), index=True
    )
    family_member_id: Mapped[int] = mapped_column(
        ForeignKey("family_members.id", ondelete="CASCADE"), index=True
    )
    liked: Mapped[bool] = mapped_column(Boolean, default=False)
    disliked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_loved: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    recipe = relationship("Recipe")
    family_member = relationship("FamilyMember")


class RecipeScenario(Base):
    __tablename__ = "recipe_scenarios"
    __table_args__ = (
        UniqueConstraint("recipe_id", "scenario", name="uq_recipe_scenarios_recipe_scenario"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    scenario: Mapped[str] = mapped_column(String(32), index=True)
    score: Mapped[float] = mapped_column(Float, default=1.0)
    source: Mapped[str] = mapped_column(String(16), default="auto")

    recipe = relationship("Recipe")


class RecipeExplanation(Base):
    """Cached deterministic explanation snapshot per recipe + scope."""

    __tablename__ = "recipe_explanations"
    __table_args__ = (
        UniqueConstraint(
            "recipe_id",
            "user_id",
            "family_id",
            name="uq_recipe_explanations_scope",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    family_id: Mapped[int | None] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), index=True, nullable=True
    )
    summary: Mapped[str] = mapped_column(String(500), default="")
    reasons_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    score_total: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    recipe = relationship("Recipe")
