from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any
from sqlalchemy.engine import make_url

from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from app.core.models import (
    CoreAccount,
    CoreAuthIdentity,
    CoreHousehold,
    CoreMembership,
    CorePerson,
    LegacyIdMapping,
    EntitlementGrant,
    EntitlementConsumption,
)
from app.food.profile_models import FoodProfile, FoodProfileFact, FoodProfileReconfirmation
from app.nutrition.target_models import NutritionTargetVersion
from app.notifications.v2_models import NotificationPreference
from app.recipes.v2_models import CanonicalArchiveFallback, CanonicalLegacyMapping, CanonicalRecipe, CanonicalRecipeVersion
from app.shopping.v2_models import ShoppingItem, ShoppingList
from app.services.shopping_item_utils import normalize_shopping_unit
from app.services.subscription_catalog import START_MENU_GENERATIONS


class ImportDisposition(StrEnum):
    IMPORT_TRUSTED = "IMPORT_TRUSTED"
    IMPORT_WITH_TRANSFORMATION = "IMPORT_WITH_TRANSFORMATION"
    RECONFIRM_REQUIRED = "RECONFIRM_REQUIRED"
    ARCHIVE_ONLY = "ARCHIVE_ONLY"
    DROP = "DROP"


class ImportPipelineError(RuntimeError):
    pass


@dataclass(frozen=True)
class ImportConfig:
    target_schema_head: str = "20260928_0020"
    target_environment: str = "DISPOSABLE"
    production_import_override: bool = False
    code_checkpoint: str = "working-tree"
    source_database_name: str = ""
    confirmed_source_snapshot: str = ""
    confirmed_target_database: str = ""


@dataclass
class ImportReport:
    batch_id: str
    source_identity: str
    target_schema_head: str
    mode: str
    environment: str
    started_at: str
    completed_at: str | None = None
    target_database: str = ""
    source_records: int = 0
    target_records_created: int = 0
    reconfirmation_count: int = 0
    archive_only_count: int = 0
    drop_count: int = 0
    rejected_count: int = 0
    unresolved_fatal_conflicts: int = 0
    classifications: dict[str, dict[str, int]] = field(default_factory=dict)
    target_counts: dict[str, int] = field(default_factory=dict)
    reconfirmations: list[dict[str, str]] = field(default_factory=list)
    collisions: list[dict[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    manifest: dict[str, str] = field(default_factory=dict)
    source_domains: dict[str, str] = field(default_factory=dict)

    def classify(self, domain: str, disposition: ImportDisposition, count: int = 1) -> None:
        bucket = self.classifications.setdefault(domain, {})
        bucket[disposition.value] = bucket.get(disposition.value, 0) + count
        self.source_records += count
        if disposition is ImportDisposition.RECONFIRM_REQUIRED:
            self.reconfirmation_count += count
        elif disposition is ImportDisposition.ARCHIVE_ONLY:
            self.archive_only_count += count
        elif disposition is ImportDisposition.DROP:
            self.drop_count += count

    def as_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "source_identity": self.source_identity,
            "target_schema_head": self.target_schema_head,
            "mode": self.mode,
            "environment": self.environment,
            "target_database": self.target_database,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "source_records": self.source_records,
            "target_records_created": self.target_records_created,
            "reconfirmation_count": self.reconfirmation_count,
            "archive_only_count": self.archive_only_count,
            "drop_count": self.drop_count,
            "rejected_count": self.rejected_count,
            "unresolved_fatal_conflicts": self.unresolved_fatal_conflicts,
            "classifications": self.classifications,
            "target_counts": self.target_counts,
            "reconfirmations": self.reconfirmations,
            "collisions": self.collisions,
            "warnings": self.warnings,
            "errors": self.errors,
            "manifest": self.manifest,
            "source_domains": self.source_domains,
        }


def load_source(path: str | Path) -> tuple[dict[str, Any], str]:
    source_path = Path(path)
    try:
        raw = source_path.read_bytes()
        source = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ImportPipelineError(f"source is not readable JSON: {source_path}") from exc
    if not isinstance(source, dict) or not isinstance(source.get("snapshot"), str):
        raise ImportPipelineError("source requires a non-sensitive snapshot identity")
    if source["snapshot"].startswith("sha256:"):
        content = {key: value for key, value in source.items() if key != "snapshot"}
        expected = hashlib.sha256(json.dumps(content, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()
        if source["snapshot"] != f"sha256:{expected}":
            raise ImportPipelineError("source snapshot content hash mismatch")
    return source, hashlib.sha256(raw).hexdigest()


def _stable_uuid7(namespace: str, legacy_id: object) -> str:
    """Create a deterministic UUID with UUIDv7 version/variant bits."""
    digest = hashlib.sha256(f"planam-w10:{namespace}:{legacy_id}".encode()).digest()
    value = int.from_bytes(digest[:16], "big")
    value &= ~(0xF << 76)
    value |= 0x7 << 76
    value &= ~(0x3 << 62)
    value |= 0x2 << 62
    return str(uuid.UUID(int=value))


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


class SelectiveImportPipeline:
    """Classify and import an explicit immutable legacy source snapshot."""

    _ONTOLOGY = {"peanut", "lactose", "gluten", "celiac"}
    _DOMAINS = (
        "accounts", "external_identities", "persons", "households", "memberships",
        "relationships", "entitlements", "food_profiles", "recipes", "plans",
        "shopping", "pantry", "receipts", "cooking", "consumption", "events",
        "notifications", "admin_sessions", "nutrition_goals", "notification_preferences",
    )
    _CUTOVER_SOURCE_DOMAINS = (
        "users", "profiles", "families", "family_members", "recipes", "shopping",
        "entitlements", "nutrition_goals", "notification_preferences", "plans",
        "pantry", "events", "cooking", "consumption", "notifications", "admin_sessions",
    )

    def __init__(self, db: Session, *, target_url: str, config: ImportConfig | None = None):
        self.db = db
        self.target_url = target_url
        self.config = config or ImportConfig()

    def precheck(self, source: dict[str, Any]) -> None:
        if self.config.target_schema_head != "20260928_0020":
            raise ImportPipelineError("target schema must be at Alembic head 20260928_0020")
        parsed = make_url(self.target_url)
        target = f"{parsed.host or ''}/{parsed.database or ''}".lower()
        production_markers = ("planam.ru", "production", "prod", "old-production")
        environment = self.config.target_environment.upper()
        if environment == "DISPOSABLE":
            if any(marker in target for marker in production_markers):
                raise ImportPipelineError("production-like target rejected in DISPOSABLE mode")
            if self.config.production_import_override:
                raise ImportPipelineError("production override is disabled in DISPOSABLE mode")
        elif environment == "CUTOVER":
            if not parsed.drivername.startswith("postgresql") or not self.config.production_import_override:
                raise ImportPipelineError("CUTOVER requires PostgreSQL and explicit authorization")
            if not self.config.source_database_name or not self.config.confirmed_target_database:
                raise ImportPipelineError("CUTOVER requires source and target database identities")
            if self.config.source_database_name.lower() == self.config.confirmed_target_database.lower():
                raise ImportPipelineError("legacy source and V2 target databases must differ")
            if source.get("source_database") != self.config.source_database_name:
                raise ImportPipelineError("source snapshot database identity mismatch")
            if source.get("snapshot") != self.config.confirmed_source_snapshot:
                raise ImportPipelineError("source snapshot confirmation mismatch")
            states = source.get("source_domains")
            if not isinstance(states, dict) or any(
                states.get(domain) not in {"SOURCE_DOMAIN_PRESENT", "SOURCE_DOMAIN_ZERO"}
                or not isinstance(source.get(domain), list)
                or (states.get(domain) == "SOURCE_DOMAIN_ZERO") != (len(source[domain]) == 0)
                for domain in self._CUTOVER_SOURCE_DOMAINS
            ):
                raise ImportPipelineError("CUTOVER source domain coverage incomplete")
        else:
            raise ImportPipelineError("unknown import environment")
        if not isinstance(source.get("snapshot"), str) or not source["snapshot"].strip():
            raise ImportPipelineError("source snapshot identity is required")

    def run(self, source: dict[str, Any], *, source_hash: str, dry_run: bool) -> ImportReport:
        self.precheck(source)
        started = datetime.now(timezone.utc)
        batch_id = _stable_uuid7("batch", source["snapshot"])
        config_hash = hashlib.sha256(_canonical_json(self.config.__dict__).encode()).hexdigest()
        report = ImportReport(
            batch_id=batch_id,
            source_identity=source["snapshot"],
            target_schema_head=self.config.target_schema_head,
            mode="DRY_RUN" if dry_run else "IMPORT",
            environment=self.config.target_environment.upper(),
            target_database=self.config.confirmed_target_database,
            started_at=started.isoformat(),
            manifest={"source_sha256": source_hash, "config_sha256": config_hash, "code_checkpoint": self.config.code_checkpoint},
            source_domains=dict(source.get("source_domains") or {}),
        )
        try:
            self._run_core(source, report, dry_run=dry_run)
            self._run_profiles(source, report, dry_run=dry_run)
            self._run_recipes(source, report, dry_run=dry_run)
            self._run_shopping(source, report, dry_run=dry_run)
            self._run_entitlements(source, report, dry_run=dry_run)
            self._run_nutrition_goals(source, report, dry_run=dry_run)
            self._run_notification_preferences(source, report, dry_run=dry_run)
            self._classify_non_promotable_domains(source, report)
            report.target_counts = self._target_counts()
            if report.unresolved_fatal_conflicts and not dry_run:
                raise ImportPipelineError("unresolved fatal source conflicts")
            if not dry_run:
                self.db.commit()
            report.completed_at = datetime.now(timezone.utc).isoformat()
            return report
        except Exception:
            if not dry_run:
                self.db.rollback()
            raise

    def _target_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for name, model in (
            ("core_accounts", CoreAccount),
            ("core_persons", CorePerson),
            ("core_households", CoreHousehold),
            ("core_memberships", CoreMembership),
            ("legacy_id_mappings", LegacyIdMapping),
            ("food_profiles", FoodProfile),
            ("food_profile_reconfirmations", FoodProfileReconfirmation),
            ("recipes_v2", CanonicalRecipe),
            ("recipe_versions", CanonicalRecipeVersion),
            ("shopping_lists", ShoppingList),
            ("shopping_items", ShoppingItem),
            ("entitlement_grants", EntitlementGrant),
            ("entitlement_consumptions", EntitlementConsumption),
            ("nutrition_target_versions", NutritionTargetVersion),
            ("notification_preferences", NotificationPreference),
        ):
            if inspect(self.db.get_bind()).has_table(name):
                counts[name] = int(self.db.scalar(select(func.count()).select_from(model)) or 0)
        return counts

    def _run_core(self, source: dict[str, Any], report: ImportReport, *, dry_run: bool) -> None:
        accounts: dict[str, str] = {}
        persons: dict[str, str] = {}
        households: dict[str, str] = {}
        for row in source.get("users", []):
            legacy_id = str(row["id"])
            account_id = self._mapped_id("users", legacy_id, "core_accounts")
            person_id = self._mapped_id("users", legacy_id, "core_persons")
            accounts[legacy_id], persons[legacy_id] = account_id, person_id
            account_exists = self.db.get(CoreAccount, account_id)
            person_exists = self.db.get(CorePerson, person_id)
            report.classify("accounts", ImportDisposition.IMPORT_WITH_TRANSFORMATION)
            report.classify("persons", ImportDisposition.IMPORT_WITH_TRANSFORMATION)
            if not dry_run:
                if account_exists is None:
                    self.db.add(CoreAccount(account_id=account_id, status="active" if not row.get("deleted") else "deleted", primary_person_id=person_id))
                    report.target_records_created += 1
                if person_exists is None:
                    self.db.add(CorePerson(person_id=person_id, display_name=row.get("display_name"), birth_date_precision="unknown", birth_date_provenance_json={"source": "legacy", "dob_fabricated": False}, status="active"))
                    report.target_records_created += 1
                self._mapping("users", legacy_id, "core_accounts", account_id, report)
                self._mapping("users", legacy_id, "core_persons", person_id, report)
            self._identity(source, row, account_id, report, dry_run=dry_run)
        for row in source.get("families", []):
            legacy_id = str(row["id"])
            household_id = self._mapped_id("families", legacy_id, "core_households")
            households[legacy_id] = household_id
            report.classify("households", ImportDisposition.IMPORT_WITH_TRANSFORMATION)
            if not dry_run and self.db.get(CoreHousehold, household_id) is None:
                self.db.add(CoreHousehold(household_id=household_id, name=row.get("name"), status="active"))
                self._mapping("families", legacy_id, "core_households", household_id, report)
                report.target_records_created += 1
        for row in source.get("family_members", []):
            legacy_id = str(row["id"])
            person_id = persons.get(str(row.get("user_id"))) or self._mapped_id("family_members", legacy_id, "core_persons")
            household_id = households.get(str(row.get("family_id")))
            if household_id is None:
                report.collisions.append({"domain": "memberships", "legacy_id": legacy_id, "reason": "missing explicit household mapping"})
                report.rejected_count += 1
                continue
            report.classify("memberships", ImportDisposition.IMPORT_WITH_TRANSFORMATION)
            membership_id = self._mapped_id("family_members", legacy_id, "core_memberships")
            if not dry_run and self.db.get(CoreMembership, membership_id) is None:
                self.db.add(CoreMembership(membership_id=membership_id, person_id=person_id, household_id=household_id, membership_status="active", role_label=row.get("role"), provenance_json={"source": "legacy", "legacy_id": legacy_id}))
                self._mapping("family_members", legacy_id, "core_memberships", membership_id, report)
                report.target_records_created += 1

    def _identity(self, source: dict[str, Any], row: dict[str, Any], account_id: str, report: ImportReport, *, dry_run: bool) -> None:
        if row.get("duplicate_candidate"):
            report.classify("external_identities", ImportDisposition.RECONFIRM_REQUIRED)
            report.reconfirmations.append({"domain": "identity", "source_id": str(row["id"]), "reason": "POSSIBLE_DUPLICATE_ACCOUNT"})
            return
        provider_subject = row.get("provider_subject")
        if not provider_subject:
            report.classify("external_identities", ImportDisposition.RECONFIRM_REQUIRED)
            report.reconfirmations.append({"domain": "identity", "source_id": str(row["id"]), "reason": "provider identity missing"})
            return
        report.classify("external_identities", ImportDisposition.IMPORT_TRUSTED)
        if not dry_run and self.db.scalar(select(CoreAuthIdentity).where(CoreAuthIdentity.provider == row.get("provider", "telegram"), CoreAuthIdentity.provider_subject == str(provider_subject))) is None:
            self.db.add(CoreAuthIdentity(auth_identity_id=self._mapped_id("users", row["id"], "external_identities"), account_id=account_id, provider=row.get("provider", "telegram"), provider_subject=str(provider_subject), provider_metadata_json={"source": "legacy", "legacy_user_id": str(row["id"])}))
            report.target_records_created += 1

    def _run_profiles(self, source: dict[str, Any], report: ImportReport, *, dry_run: bool) -> None:
        for row in source.get("profiles", []):
            person_id = self._mapped_id("users", str(row["user_id"]), "core_persons")
            profile_id = self._mapped_id("user_profiles", str(row["id"]), "food_profiles")
            report.classify("food_profiles", ImportDisposition.IMPORT_WITH_TRANSFORMATION)
            if not dry_run and self.db.get(FoodProfile, profile_id) is None:
                self.db.add(FoodProfile(food_profile_id=profile_id, person_id=person_id, profile_status="ACTIVE", provenance_json={"source": "user_profiles", "legacy_id": str(row["id"])}))
                self._mapping("user_profiles", str(row["id"]), "food_profiles", profile_id, report)
                report.target_records_created += 1
            for value in row.get("allergies", []):
                key = str(value).strip().lower()
                if key in self._ONTOLOGY:
                    report.classify("food_profiles", ImportDisposition.IMPORT_TRUSTED)
                    if not dry_run and self.db.scalar(select(FoodProfileFact).where(FoodProfileFact.food_profile_id == profile_id, FoodProfileFact.fact_type == "allergy", FoodProfileFact.fact_key == key)) is None:
                        self.db.add(FoodProfileFact(fact_id=self._mapped_id("food_profile_facts", f"{row['id']}:allergy:{key}", "food_profile_facts"), food_profile_id=profile_id, fact_type="allergy", fact_key=key, knowledge_state="KNOWN_PRESENT", value_json={"ontology_key": key}, provenance_json={"source": "legacy", "deterministic_mapping": True}, source_kind="LEGACY_MIGRATED", source_legacy_table="user_profiles", source_legacy_id_text=str(row["id"]), confirmation_status="UNCONFIRMED"))
                        report.target_records_created += 1
                else:
                    self._reconfirm(profile_id, "allergy", key or "unknown", "ambiguous_or_free_text_allergy", str(row["id"]), report, dry_run=dry_run)
            if row.get("medical_notes") or row.get("age") is not None:
                self._reconfirm(profile_id, "profile", "legacy_sensitive_fact", "reconfirmation_required", str(row["id"]), report, dry_run=dry_run)

    def _reconfirm(self, profile_id: str, fact_type: str, fact_key: str, reason: str, legacy_id: str, report: ImportReport, *, dry_run: bool) -> None:
        report.classify("food_profiles", ImportDisposition.RECONFIRM_REQUIRED)
        report.reconfirmations.append({"domain": "food_profile", "source_id": legacy_id, "reason": reason})
        if not dry_run and self.db.scalar(select(FoodProfileReconfirmation).where(FoodProfileReconfirmation.food_profile_id == profile_id, FoodProfileReconfirmation.fact_type == fact_type, FoodProfileReconfirmation.fact_key == fact_key, FoodProfileReconfirmation.reason == reason)) is None:
            self.db.add(FoodProfileReconfirmation(reconfirmation_id=self._mapped_id("reconfirmations", f"{legacy_id}:{fact_type}:{fact_key}", "food_profile_reconfirmations"), food_profile_id=profile_id, fact_type=fact_type, fact_key=fact_key, reason=reason, status="PENDING", provenance_json={"source": "legacy", "legacy_id": legacy_id}, source_kind="LEGACY_MIGRATED", source_legacy_table="user_profiles", source_legacy_id_text=legacy_id))
            report.target_records_created += 1

    def _run_recipes(self, source: dict[str, Any], report: ImportReport, *, dry_run: bool) -> None:
        for row in source.get("recipes", []):
            legacy_id = str(row["id"])
            if not row.get("gold_v3_validated"):
                report.classify("recipes", ImportDisposition.ARCHIVE_ONLY)
                report.warnings.append(f"recipe {legacy_id} retained as archive fallback: Gold V3 validation unavailable")
                if not dry_run and self.db.get(CanonicalArchiveFallback, int(legacy_id)) is None:
                    self.db.add(CanonicalArchiveFallback(legacy_recipe_id=int(legacy_id), archive_payload_json={"legacy_id": legacy_id, "title": row.get("title"), "reason": "validation_unavailable"}, source_kind="LEGACY_ARCHIVE"))
                continue
            report.classify("recipes", ImportDisposition.IMPORT_WITH_TRANSFORMATION)
            recipe_id = self._mapped_id("recipes", legacy_id, "recipes_v2")
            version_id = self._mapped_id("recipes", legacy_id, "recipe_versions")
            if not dry_run and self.db.get(CanonicalRecipe, recipe_id) is None:
                self.db.add(CanonicalRecipe(recipe_id=recipe_id, status="DRAFT", canonical_key=f"legacy:{legacy_id}"))
                self.db.add(CanonicalRecipeVersion(recipe_version_id=version_id, recipe_id=recipe_id, version_number=1, lifecycle_status="DRAFT", title=str(row.get("title") or "Untitled"), source_provenance_json={"source": "legacy", "legacy_id": legacy_id}, gold_v3_validation_json={"validated": True}, gold_v3_payload_json=row.get("gold_v3_payload") or {}))
                self.db.add(CanonicalLegacyMapping(mapping_id=_stable_uuid7("recipe_mapping", legacy_id), legacy_recipe_id=int(legacy_id), canonical_recipe_id=recipe_id, canonical_version_id=version_id, mapping_status="MAPPED", mapping_reason="validated_gold_v3", provenance_json={"source": "legacy", "legacy_id": legacy_id}))
                report.target_records_created += 2

    def _run_shopping(self, source: dict[str, Any], report: ImportReport, *, dry_run: bool) -> None:
        users = {str(row["id"]) for row in source.get("users", [])}
        families = {str(row["id"]) for row in source.get("families", [])}
        for row in source.get("shopping", []):
            legacy_id = str(row["id"])
            family_id = row.get("family_id")
            user_id = row.get("user_id")
            if family_id is not None:
                if str(family_id) not in families:
                    report.classify("shopping", ImportDisposition.RECONFIRM_REQUIRED)
                    report.unresolved_fatal_conflicts += 1
                    continue
                household_id = self._mapped_id("families", str(family_id), "core_households")
                person_id = None
            elif user_id is not None and str(user_id) in users:
                household_id = None
                person_id = self._mapped_id("users", str(user_id), "core_persons")
            else:
                report.classify("shopping", ImportDisposition.RECONFIRM_REQUIRED)
                if self.config.target_environment.upper() == "CUTOVER":
                    report.unresolved_fatal_conflicts += 1
                continue
            items = row.get("items")
            if not isinstance(items, list):
                report.classify("shopping", ImportDisposition.RECONFIRM_REQUIRED)
                report.unresolved_fatal_conflicts += 1
                continue
            list_id = self._mapped_id("family_shopping_lists", legacy_id, "shopping_lists")
            report.classify("shopping", ImportDisposition.IMPORT_WITH_TRANSFORMATION)
            existing = self.db.get(ShoppingList, list_id)
            if existing is not None and (existing.person_id != person_id or existing.household_id != household_id):
                report.unresolved_fatal_conflicts += 1
                continue
            if not dry_run and existing is None:
                self.db.add(ShoppingList(
                    shopping_list_id=list_id, person_id=person_id, household_id=household_id,
                    status="ACTIVE", idempotency_key=f"legacy:{legacy_id}",
                ))
                report.target_records_created += 1
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    report.classify("shopping", ImportDisposition.RECONFIRM_REQUIRED)
                    report.unresolved_fatal_conflicts += 1
                    continue
                source_item_id = str(item.get("id") or index)
                name = str(item.get("name") or "").strip()
                if not name or len(name) > 240:
                    report.classify("shopping", ImportDisposition.RECONFIRM_REQUIRED)
                    report.unresolved_fatal_conflicts += 1
                    continue
                raw_unit = str(item.get("unit") or "").strip()
                unit = normalize_shopping_unit(raw_unit) or None
                raw_quantity = str(item.get("quantity") or "").strip().replace(",", ".")
                try:
                    quantity = float(raw_quantity)
                except ValueError:
                    quantity = None
                if quantity is not None and (not 0 < quantity < 1_000_000_000):
                    quantity = None
                uncertainty = "KNOWN" if quantity is not None and unit else "UNKNOWN"
                if uncertainty == "UNKNOWN":
                    quantity = None
                state = "CHECKED" if item.get("checked") is True else "NEEDED"
                report.classify("shopping", ImportDisposition.IMPORT_WITH_TRANSFORMATION)
                item_id = self._mapped_id("family_shopping_items", f"{legacy_id}:{source_item_id}", "shopping_items")
                if not dry_run and self.db.get(ShoppingItem, item_id) is None:
                    self.db.add(ShoppingItem(
                        shopping_item_id=item_id, shopping_list_id=list_id, display_text=name,
                        quantity=quantity, unit=unit, uncertainty=uncertainty,
                        category=str(item.get("category"))[:64] if item.get("category") else None,
                        state=state, source_kind="LEGACY_MIGRATED",
                        provenance_json={"legacy_table": "family_shopping_lists", "legacy_list_id": legacy_id,
                                         "legacy_item_id": source_item_id, "raw_quantity": item.get("quantity"),
                                         "raw_unit": raw_unit, "checked": item.get("checked"),
                                         "added_to_pantry": item.get("added_to_pantry"),
                                         "owner_scope": "PERSON" if person_id else "HOUSEHOLD"},
                        idempotency_key=f"legacy:{hashlib.sha256(f'{legacy_id}:{source_item_id}'.encode()).hexdigest()[:32]}",
                    ))
                    report.target_records_created += 1

    @staticmethod
    def _instant(value: object) -> datetime | None:
        if isinstance(value, datetime):
            result = value
        elif isinstance(value, str):
            try:
                result = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        else:
            return None
        return result if result.tzinfo is not None else None

    def _run_entitlements(self, source: dict[str, Any], report: ImportReport, *, dry_run: bool) -> None:
        users = {str(row["id"]) for row in source.get("users", [])}
        now = datetime.now(timezone.utc)
        for row in source.get("entitlements", []):
            legacy_id = str(row["id"])
            status = str(row.get("status") or "").lower()
            if status in {"expired", "cancelled"}:
                report.classify("entitlements", ImportDisposition.ARCHIVE_ONLY)
                continue
            account_id = self._mapped_id("users", str(row.get("user_id")), "core_accounts")
            start = self._instant(row.get("started_at"))
            end = self._instant(row.get("trial_ends_at" if status == "trial" else "current_period_ends_at"))
            if (status not in {"trial", "active", "manually_granted"}
                    or row.get("plan_code") != "start" or str(row.get("user_id")) not in users
                    or start is None or end is None or end <= now or end <= start
                    or row.get("family_id") is not None):
                report.classify("entitlements", ImportDisposition.RECONFIRM_REQUIRED)
                report.reconfirmations.append({"domain": "entitlements", "source_id": legacy_id, "reason": "commercial_state_unmapped"})
                report.unresolved_fatal_conflicts += 1
                continue
            used = row.get("menu_generations_used")
            if not isinstance(used, int) or used < 0:
                report.classify("entitlements", ImportDisposition.RECONFIRM_REQUIRED)
                report.unresolved_fatal_conflicts += 1
                continue
            report.classify("entitlements", ImportDisposition.IMPORT_WITH_TRANSFORMATION)
            grant_id = self._mapped_id("user_subscriptions", legacy_id, "entitlement_grants")
            if not dry_run and self.db.get(EntitlementGrant, grant_id) is None:
                self.db.add(EntitlementGrant(
                    grant_id=grant_id, account_id=account_id, capability="planner.generate",
                    limit_value=START_MENU_GENERATIONS, effective_from=start, effective_to=end,
                    grant_status="active", source="legacy_subscription",
                    idempotency_key=f"legacy-subscription:{legacy_id}",
                    provenance_json={"legacy_table": "user_subscriptions", "legacy_id": legacy_id,
                                     "status": status, "plan_code": "start", "trial_ends_at": end.isoformat()},
                ))
                report.target_records_created += 1
                if used:
                    self.db.add(EntitlementConsumption(
                        consumption_id=self._mapped_id("user_subscriptions", legacy_id, "entitlement_consumptions"),
                        grant_id=grant_id, amount=used, idempotency_key=f"legacy-usage:{legacy_id}",
                        provenance_json={"legacy_table": "user_subscriptions", "legacy_id": legacy_id},
                    ))
                    report.target_records_created += 1

    def _run_nutrition_goals(self, source: dict[str, Any], report: ImportReport, *, dry_run: bool) -> None:
        users = {str(row["id"]) for row in source.get("users", [])}
        units = {"calories_target": "kcal", "protein_target_g": "g", "fat_target_g": "g",
                 "carbs_target_g": "g", "fiber_target_g": "g", "water_target_ml": "ml"}
        for row in source.get("nutrition_goals", []):
            legacy_id = str(row["id"])
            values = {key: {"value": row[key], "unit": unit} for key, unit in units.items() if row.get(key) is not None}
            if (str(row.get("user_id")) not in users or row.get("person_id") is not None
                    or row.get("family_id") is not None or not values
                    or any(not isinstance(v["value"], int) or v["value"] <= 0 for v in values.values())):
                report.classify("nutrition_goals", ImportDisposition.RECONFIRM_REQUIRED)
                continue
            report.classify("nutrition_goals", ImportDisposition.IMPORT_WITH_TRANSFORMATION)
            target_id = self._mapped_id("nutrition_targets", legacy_id, "nutrition_target_versions")
            effective_from = self._instant(row.get("created_at"))
            if effective_from is None:
                report.classify("nutrition_goals", ImportDisposition.RECONFIRM_REQUIRED)
                report.reconfirmations.append({
                    "domain": "nutrition_goals",
                    "source_id": legacy_id,
                    "reason": "missing_deterministic_effective_timestamp",
                })
                continue
            if not dry_run and self.db.get(NutritionTargetVersion, target_id) is None:
                self.db.add(NutritionTargetVersion(
                    target_id=target_id,
                    person_id=self._mapped_id("users", str(row["user_id"]), "core_persons"),
                    target_kind="daily_nutrition", context_key="legacy_current",
                    effective_from=effective_from,
                    target_values_json={"basis": "daily", "metrics": values, "goal_type": row.get("goal_type")},
                    origin="LEGACY_ESTIMATOR", provenance_status="UNREVIEWED",
                    provenance_json={"legacy_table": "nutrition_targets", "legacy_id": legacy_id,
                                     "source_units": "legacy_column_names", "clinical_authority": False},
                ))
                report.target_records_created += 1

    def _run_notification_preferences(self, source: dict[str, Any], report: ImportReport, *, dry_run: bool) -> None:
        for row in source.get("notification_preferences", []):
            user_id = str(row.get("user_id"))
            if not row.get("notifications_onboarded") or not any(
                isinstance(row.get(key), bool) for key in ("buy_reminder_enabled", "cook_reminder_enabled")
            ):
                report.classify("notification_preferences", ImportDisposition.RECONFIRM_REQUIRED)
                report.reconfirmations.append({"domain": "notification_preferences", "source_id": str(row["id"]),
                                               "reason": "notification_intent_not_explicit"})
                continue
            report.classify("notification_preferences", ImportDisposition.IMPORT_WITH_TRANSFORMATION)
            preference_id = self._mapped_id("notification_settings", str(row["id"]), "notification_preferences")
            if not dry_run and self.db.get(NotificationPreference, preference_id) is None:
                self.db.add(NotificationPreference(
                    preference_id=preference_id, subject_kind="PERSON",
                    subject_id=self._mapped_id("users", user_id, "core_persons"), channel="telegram",
                    enabled=True, shopping_enabled=row.get("buy_reminder_enabled"),
                    cooking_enabled=row.get("cook_reminder_enabled"), timezone=row.get("timezone"),
                    idempotency_key=f"legacy-notification-settings:{row['id']}",
                    request_hash=hashlib.sha256(
                        json.dumps({"legacy_table": "notification_settings", "legacy_id": str(row["id"])}, sort_keys=True).encode()
                    ).hexdigest(),
                ))
                report.target_records_created += 1

    def _classify_non_promotable_domains(self, source: dict[str, Any], report: ImportReport) -> None:
        for domain, rows in ((name, source.get(name, [])) for name in self._DOMAINS):
            if domain in {"accounts", "external_identities", "persons", "households", "memberships", "food_profiles", "recipes", "shopping", "entitlements", "nutrition_goals", "notification_preferences"}:
                continue
            for row in rows:
                legacy_id = str(row.get("id", "unknown"))
                if domain == "admin_sessions" or domain == "notifications":
                    report.classify(domain, ImportDisposition.DROP)
                elif domain == "events" and row.get("allergies_note"):
                    report.classify(domain, ImportDisposition.RECONFIRM_REQUIRED)
                    report.reconfirmations.append({"domain": "event", "source_id": legacy_id, "reason": "legacy_event_allergy_note"})
                else:
                    report.classify(domain, ImportDisposition.ARCHIVE_ONLY)

    def _mapped_id(self, legacy_table: str, legacy_id: str, target_table: str) -> str:
        existing = self.db.scalar(select(LegacyIdMapping).where(LegacyIdMapping.legacy_table == legacy_table, LegacyIdMapping.legacy_id_text == str(legacy_id), LegacyIdMapping.target_table == target_table))
        return existing.target_id_uuid if existing is not None else _stable_uuid7(target_table, legacy_id)

    def _mapping(self, legacy_table: str, legacy_id: str, target_table: str, target_id: str, report: ImportReport) -> None:
        existing = self.db.scalar(select(LegacyIdMapping).where(LegacyIdMapping.legacy_table == legacy_table, LegacyIdMapping.legacy_id_text == str(legacy_id), LegacyIdMapping.target_table == target_table))
        if existing is not None:
            if existing.target_id_uuid != target_id:
                report.collisions.append({"domain": target_table, "legacy_id": str(legacy_id), "reason": "mapping collision"})
                report.unresolved_fatal_conflicts += 1
            return
        self.db.add(LegacyIdMapping(mapping_id=_stable_uuid7("legacy_mapping", f"{legacy_table}:{legacy_id}:{target_table}"), legacy_table=legacy_table, legacy_id_text=str(legacy_id), target_table=target_table, target_id_uuid=target_id, confidence="source_backed", migration_status="auto_migrated_with_provenance", provenance_json={"source": legacy_table, "legacy_id": str(legacy_id)}))
