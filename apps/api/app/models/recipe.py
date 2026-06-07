from datetime import datetime

from sqlalchemy import (
    Boolean,
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


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    original_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    normalized_title: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    display_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    meal_type: Mapped[str] = mapped_column(String(32), index=True)
    category: Mapped[str] = mapped_column(String(32), index=True, default="main")
    cuisine: Mapped[str | None] = mapped_column(String(64), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(16), default="easy")
    cooking_time_minutes: Mapped[int] = mapped_column(Integer, default=30)
    prep_time_minutes: Mapped[int] = mapped_column(Integer, default=30)
    servings: Mapped[int] = mapped_column(Integer, default=4)
    calories_per_serving: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fiber_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    sugar_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_type: Mapped[str] = mapped_column(String(16), default="manual")
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    hero_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_drink: Mapped[bool] = mapped_column(Boolean, default=False)
    is_alcoholic: Mapped[bool] = mapped_column(Boolean, default=False)
    alcohol_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    caffeine_mg: Mapped[float | None] = mapped_column(Float, nullable=True)
    suitable_for_children: Mapped[bool] = mapped_column(Boolean, default=True)
    suitable_for_sport: Mapped[bool] = mapped_column(Boolean, default=False)
    suitable_for_event: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    diets: Mapped[list] = mapped_column(JSONB, default=list)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    ingredients: Mapped[list] = mapped_column(JSONB, default=list)
    steps: Mapped[list] = mapped_column(JSONB, default=list)
    # Recipe-level nutrition summary (nullable; computed by
    # calculate_recipe_nutrition_summary.py). Additive — does NOT replace the
    # legacy calories_per_serving / protein_g / fat_g / carbs_g fields.
    nutrition_kcal_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    nutrition_protein_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    nutrition_fat_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    nutrition_carbs_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    nutrition_kcal_per_serving: Mapped[float | None] = mapped_column(Float, nullable=True)
    nutrition_protein_per_serving: Mapped[float | None] = mapped_column(Float, nullable=True)
    nutrition_fat_per_serving: Mapped[float | None] = mapped_column(Float, nullable=True)
    nutrition_carbs_per_serving: Mapped[float | None] = mapped_column(Float, nullable=True)
    nutrition_servings: Mapped[float | None] = mapped_column(Float, nullable=True)
    nutrition_serving_size_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    nutrition_confidence: Mapped[str | None] = mapped_column(String(24), nullable=True)
    nutrition_coverage_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    nutrition_calculated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    nutrition_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nutrition_needs_review: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    nutrition_review_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    favorites = relationship("RecipeFavorite", back_populates="recipe")
    ingredient_rows = relationship(
        "RecipeIngredientRow",
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="RecipeIngredientRow.id",
    )
    step_rows = relationship(
        "RecipeStepRow",
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="RecipeStepRow.step_number",
    )
    tag_rows = relationship(
        "RecipeTagRow", back_populates="recipe", cascade="all, delete-orphan"
    )
    allergen_rows = relationship(
        "RecipeAllergenRow", back_populates="recipe", cascade="all, delete-orphan"
    )
    restriction_rows = relationship(
        "RecipeRestrictionRow", back_populates="recipe", cascade="all, delete-orphan"
    )
    ratings = relationship("RecipeRating", back_populates="recipe")


class RecipeIngredientRow(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    quantity: Mapped[str] = mapped_column(String(32), default="1")
    unit: Mapped[str] = mapped_column(String(32), default="шт")
    category: Mapped[str] = mapped_column(String(32), default="other")
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Ingredient quality model (nullable; populated by migrate_to_taste_ingredients.py).
    # Not exposed by API serializers yet — added for shopping/nutrition/photo pipelines.
    quantity_mode: Mapped[str | None] = mapped_column(String(16), nullable=True)
    quantity_text: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_to_taste: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    nutrition_precision: Mapped[str | None] = mapped_column(String(24), nullable=True)
    shopping_priority: Mapped[str | None] = mapped_column(String(16), nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    needs_review_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    photo_visibility: Mapped[str | None] = mapped_column(String(16), nullable=True)
    manual_review_status: Mapped[str | None] = mapped_column(String(16), nullable=True)

    recipe = relationship("Recipe", back_populates="ingredient_rows")


class RecipeStepRow(Base):
    __tablename__ = "recipe_steps"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    step_number: Mapped[int] = mapped_column(Integer, default=1)
    text: Mapped[str] = mapped_column(Text)

    recipe = relationship("Recipe", back_populates="step_rows")


class RecipeTagRow(Base):
    __tablename__ = "recipe_tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    tag: Mapped[str] = mapped_column(String(64), index=True)

    recipe = relationship("Recipe", back_populates="tag_rows")


class RecipeAllergenRow(Base):
    __tablename__ = "recipe_allergens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    allergen: Mapped[str] = mapped_column(String(64), index=True)

    recipe = relationship("Recipe", back_populates="allergen_rows")


class RecipeRestrictionRow(Base):
    __tablename__ = "recipe_restrictions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    restriction: Mapped[str] = mapped_column(String(64), index=True)

    recipe = relationship("Recipe", back_populates="restriction_rows")


class RecipeRating(Base):
    __tablename__ = "recipe_ratings"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "recipe_id", name="uq_recipe_rating_user_recipe"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    family_id: Mapped[int | None] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), index=True, nullable=True
    )
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    cooked_count: Mapped[int] = mapped_column(Integer, default=0)
    last_cooked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    recipe = relationship("Recipe", back_populates="ratings")


class RecipeFavorite(Base):
    __tablename__ = "recipe_favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "recipe_id", name="uq_recipe_favorite_user_recipe"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user = relationship("User", back_populates="recipe_favorites")
    recipe = relationship("Recipe", back_populates="favorites")


class RecipeImportJob(Base):
    __tablename__ = "recipe_import_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(String(64))
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    imported_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
