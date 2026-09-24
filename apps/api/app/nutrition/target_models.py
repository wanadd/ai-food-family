from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NutritionTargetVersion(Base):
    """Derived, person-scoped target with database-owned temporal integrity."""

    __tablename__ = "nutrition_target_versions"
    __table_args__ = (
        UniqueConstraint("person_id", "target_kind", "context_key", "effective_from", name="uq_nutrition_target_v2_start"),
        CheckConstraint("effective_to IS NULL OR effective_to > effective_from", name="ck_nutrition_target_v2_period"),
        CheckConstraint("origin IN ('EVIDENCE_BACKED', 'MANUAL', 'CLINICIAN', 'LEGACY_ESTIMATOR')", name="ck_nutrition_target_v2_origin"),
        CheckConstraint("provenance_status IN ('UNREVIEWED', 'REVIEWED', 'AUTHORITATIVE', 'SUPERSEDED')", name="ck_nutrition_target_v2_provenance"),
        Index("ix_nutrition_target_v2_person_scope", "person_id", "target_kind", "context_key", "effective_from"),
    )

    target_id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), primary_key=True)
    person_id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), ForeignKey("core_persons.person_id", ondelete="CASCADE"), nullable=False)
    target_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    context_key: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    supersedes_id: Mapped[str | None] = mapped_column(PG_UUID(as_uuid=False), ForeignKey("nutrition_target_versions.target_id", ondelete="SET NULL"), nullable=True)
    target_values_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    origin: Mapped[str] = mapped_column(String(32), nullable=False)
    provenance_status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNREVIEWED")
    source_rule_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    calculation_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    evaluation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
