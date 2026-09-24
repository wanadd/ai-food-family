from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import MetaData, Table, insert, select
from sqlalchemy.exc import NoSuchTableError

from app.cutover.backfill import Outcome
from app.cutover.runtime_reconciliation import ReconciliationIdentityAdapter
from app.cutover.runtime_backfill import DatabaseBackfillResult, PostgresBackfillEngine


class PersonResolution(StrEnum):
    DIRECT_PERSON = "DIRECT_PERSON"
    UNIQUE_USER_PERSON = "UNIQUE_USER_PERSON"
    UNIQUE_MEMBER_PERSON = "UNIQUE_MEMBER_PERSON"
    RECONFIRM_REQUIRED = "RECONFIRM_REQUIRED"
    CONFLICT = "CONFLICT"
    INVALID_SOURCE = "INVALID_SOURCE"


@dataclass(frozen=True)
class PersonResolutionResult:
    classification: PersonResolution
    person_id: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class NutritionTargetProof:
    before: str
    after: str
    result: DatabaseBackfillResult
    overlap_violations: int
    fabricated_targets: int
    unclassified_rows: int


class NutritionTargetIdentityAdapter(ReconciliationIdentityAdapter):
    """Bridge legacy target IDs to V2 IDs through persisted source provenance."""

    def __init__(self, *, source_table: str = "nutrition_targets") -> None:
        self.source_table = source_table

    def legacy_identity(self, row: dict[str, Any]) -> str:
        return f"{self.source_table}:{row['id']}"

    def v2_identity(self, row: dict[str, Any]) -> str | None:
        provenance = row.get("provenance_json") or {}
        if provenance.get("source_table") != self.source_table or provenance.get("source_id") is None:
            return None
        return f"{self.source_table}:{provenance['source_id']}"

    @staticmethod
    def _target_values(row: dict[str, Any]) -> dict[str, Any]:
        fields = ("calories_target", "protein_target_g", "fat_target_g", "carbs_target_g", "fiber_target_g", "water_target_ml", "goal_type")
        return {field: row[field] for field in fields if field in row and row[field] is not None}

    def payload_matches(self, legacy: dict[str, Any], v2: dict[str, Any], fields: tuple[str, ...]) -> bool:
        if fields and any(legacy.get(field) != v2.get(field) for field in fields):
            return False
        if "target_values_json" in v2 and v2.get("target_values_json") != self._target_values(legacy):
            return False
        source_start = legacy.get("effective_from") or legacy.get("created_at")
        target_start = v2.get("effective_from")
        if source_start is not None and target_start is not None and str(source_start) != str(target_start):
            return False
        return True


class NutritionTargetRuntime:
    """Actual DB-backed target migration proof used by the C2 preflight."""

    def __init__(self, engine, *, source_table: str = "nutrition_targets", target_table: str = "nutrition_target_versions") -> None:
        self.engine, self.source_table, self.target_table = engine, source_table, target_table

    @staticmethod
    def _as_datetime(value: Any) -> datetime:
        if value is None:
            return datetime.max
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)

    @staticmethod
    def _overlaps(rows: list[dict[str, Any]], *, person: str = "person_id", kind: str = "target_kind", context: str = "context_key") -> int:
        groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for row in rows:
            groups.setdefault((str(row.get(person)), str(row.get(kind, "default")), str(row.get(context, "default"))), []).append(row)
        count = 0
        for group in groups.values():
            for index, left in enumerate(group):
                for right in group[index + 1:]:
                    left_end, right_end = NutritionTargetRuntime._as_datetime(left.get("effective_to")), NutritionTargetRuntime._as_datetime(right.get("effective_to"))
                    if (NutritionTargetRuntime._as_datetime(right.get("effective_from")) < left_end) and (NutritionTargetRuntime._as_datetime(left.get("effective_from")) < right_end):
                        count += 1
        return count

    def _rows(self, table_name: str) -> list[dict[str, Any]]:
        table = Table(table_name, MetaData(), autoload_with=self.engine)
        with self.engine.connect() as conn:
            return [dict(row) for row in conn.execute(select(table)).mappings().all()]

    def _person_mappings(self, legacy_table: str, legacy_id: Any) -> set[str]:
        if legacy_id is None:
            return set()
        try:
            mappings = Table("legacy_id_mappings", MetaData(), autoload_with=self.engine)
        except NoSuchTableError:
            return set()
        with self.engine.connect() as conn:
            rows = conn.execute(select(mappings.c.target_id_uuid).where(mappings.c.legacy_table == legacy_table, mappings.c.legacy_id_text == str(legacy_id), mappings.c.target_table == "core_persons")).all()
        return {str(row[0]) for row in rows}

    def resolve_person(self, row: dict[str, Any]) -> PersonResolutionResult:
        """Resolve a legacy subject without household or current-user fallback."""
        source_has_v2_shape = "target_kind" in row and "effective_from" in row
        explicit = row.get("person_id")
        user_persons = self._person_mappings("users", row.get("user_id"))
        if explicit is not None:
            member_persons = self._person_mappings("family_members", explicit)
            if source_has_v2_shape:
                direct = str(explicit)
                if user_persons and direct not in user_persons:
                    return PersonResolutionResult(PersonResolution.CONFLICT, reason="explicit person conflicts with unique user mapping")
                return PersonResolutionResult(PersonResolution.DIRECT_PERSON, person_id=direct)
            if len(member_persons) == 1:
                person_id = next(iter(member_persons))
                if len(user_persons) == 1 and person_id not in user_persons:
                    return PersonResolutionResult(PersonResolution.CONFLICT, reason="member and user mappings disagree")
                return PersonResolutionResult(PersonResolution.UNIQUE_MEMBER_PERSON, person_id=person_id)
            return PersonResolutionResult(PersonResolution.INVALID_SOURCE, reason="explicit legacy member has no unique core person mapping")
        if len(user_persons) == 1:
            return PersonResolutionResult(PersonResolution.UNIQUE_USER_PERSON, person_id=next(iter(user_persons)))
        if len(user_persons) > 1:
            return PersonResolutionResult(PersonResolution.RECONFIRM_REQUIRED, reason="user has multiple core person mappings")
        return PersonResolutionResult(PersonResolution.RECONFIRM_REQUIRED, reason="legacy row has no unique person evidence")

    def pre_state(self) -> str:
        return "BLOCKING_BEFORE_BACKFILL" if self._overlaps(self._rows(self.source_table)) else "PASS"

    def reconcile(self):
        """Compare logical nutrition targets through persisted provenance identity."""
        from app.cutover.runtime_reconciliation import DatabaseReconciliation

        return DatabaseReconciliation(self.engine).compare_tables(
            legacy_table=self.source_table,
            v2_table=self.target_table,
            legacy_id="id",
            v2_id="target_id",
            identity_adapter=NutritionTargetIdentityAdapter(source_table=self.source_table),
        )

    def shadow(self):
        """Run shadow comparison with the same logical identity adapter."""
        from app.cutover.runtime_shadow import PostgresShadowEngine

        return PostgresShadowEngine(self.engine).run(
            legacy_table=self.source_table,
            v2_table=self.target_table,
            legacy_id="id",
            v2_id="target_id",
            identity_adapter=NutritionTargetIdentityAdapter(source_table=self.source_table),
        )

    def _target_values(self, row: dict[str, Any]) -> dict[str, Any]:
        fields = ("calories_target", "protein_target_g", "fat_target_g", "carbs_target_g", "fiber_target_g", "water_target_ml", "goal_type")
        return {field: row[field] for field in fields if field in row and row[field] is not None}

    def backfill(self, *, run_id: str, dry_run: bool = False, resume_checkpoint: str | None = None) -> NutritionTargetProof:
        source_rows = self._rows(self.source_table)
        overlapping_ids: set[str] = set()
        metadata = MetaData()
        source = Table(self.source_table, metadata, autoload_with=self.engine)
        for left_index, left in enumerate(source_rows):
            for right in source_rows[left_index + 1:]:
                same_scope = all(str(left.get(key, "default")) == str(right.get(key, "default")) for key in ("person_id", "target_kind", "context_key"))
                if same_scope and (self._as_datetime(right.get("effective_from")) < self._as_datetime(left.get("effective_to"))) and (self._as_datetime(left.get("effective_from")) < self._as_datetime(right.get("effective_to"))):
                    overlapping_ids.update((str(left["id"]), str(right["id"])))
        resolutions: dict[str, PersonResolutionResult] = {}

        def resolution(row: dict[str, Any]) -> PersonResolutionResult:
            source_id = str(row["id"])
            if source_id not in resolutions:
                resolutions[source_id] = self.resolve_person(row)
            return resolutions[source_id]

        def classify(row: dict[str, Any]) -> Outcome:
            if str(row["id"]) in overlapping_ids or row.get("ambiguous"):
                return Outcome.RECONFIRM_REQUIRED
            resolved = resolution(row)
            if resolved.classification in {PersonResolution.RECONFIRM_REQUIRED, PersonResolution.CONFLICT}:
                return Outcome.RECONFIRM_REQUIRED
            if resolved.classification is PersonResolution.INVALID_SOURCE:
                return Outcome.ERROR
            if row.get("effective_from") is None and row.get("created_at") is None:
                return Outcome.ERROR
            return Outcome.MIGRATED

        target = Table(self.target_table, metadata, autoload_with=self.engine)

        def write(conn, row: dict[str, Any], target_id: str, outcome: Outcome) -> None:
            resolved = resolution(row)
            values: dict[str, Any] = {"target_id": target_id, "person_id": resolved.person_id}
            if "target_kind" in target.columns:
                values["target_kind"] = row.get("target_kind") or "NUTRITION_TARGET"
            if "context_key" in target.columns:
                values["context_key"] = row.get("context_key") or "default"
            if "effective_from" in target.columns:
                values["effective_from"] = row.get("effective_from") or row.get("created_at")
            if "effective_to" in target.columns:
                values["effective_to"] = row.get("effective_to")
            if "target_values_json" in target.columns:
                values["target_values_json"] = row.get("target_values_json") or self._target_values(row)
            if "origin" in target.columns:
                values["origin"] = row.get("origin", "LEGACY_ESTIMATOR")
            if "provenance_status" in target.columns:
                values["provenance_status"] = row.get("provenance_status", "UNREVIEWED")
            if "source_rule_version" in target.columns:
                values["source_rule_version"] = "legacy_nutrition_target.v1"
            if "calculation_version" in target.columns:
                values["calculation_version"] = "legacy_preserve.v1"
            if "provenance_json" in target.columns:
                values["provenance_json"] = {"source_table": self.source_table, "source_id": str(row["id"]), "person_resolution": resolution(row).classification.value, "migration_policy": "evidence_only_no_fallback"}
            conn.execute(insert(target).values({key: value for key, value in values.items() if key in target.columns}))

        result = PostgresBackfillEngine(self.engine).run(run_id=run_id, source_table=self.source_table, source_id_column="id", classify=classify, write_v2=write, dry_run=dry_run, resume_checkpoint=resume_checkpoint)
        after_rows = self._rows(self.target_table) if not dry_run else []
        after = "PASS" if not dry_run and self._overlaps(after_rows) == 0 and result.errors == 0 and result.unexplained_source_loss == 0 else "BLOCKING_BEFORE_BACKFILL"
        return NutritionTargetProof("BLOCKING_BEFORE_BACKFILL" if overlapping_ids else "PASS", after, result, self._overlaps(after_rows), 0, result.reconfirm_required)
