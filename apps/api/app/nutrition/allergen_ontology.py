"""Typed allergen and celiac safety foundation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Literal

ProfileSafetyKind = Literal[
    "allergy",
    "intolerance",
    "medical_condition",
    "diet",
    "religious_cultural",
    "preference",
    "goal",
    "allergy_or_avoidance_legacy",
    "intolerance_or_diet_legacy",
    "diet_legacy",
]
RelationType = Literal["contains", "may_contain", "cross_contact", "unknown"]
AllergenProvenanceStatus = Literal[
    "external_verified",
    "product_label",
    "curated_reviewed",
    "recipe_derived",
    "legacy_inferred",
    "ai_unverified",
    "unknown",
]
GlutenFreeStatus = Literal[
    "verified_gluten_free",
    "not_gluten_free",
    "cross_contact_risk",
    "unknown",
]

PROFILE_SAFETY_KINDS = frozenset(
    {
        "allergy",
        "intolerance",
        "medical_condition",
        "diet",
        "religious_cultural",
        "preference",
        "goal",
        "allergy_or_avoidance_legacy",
        "intolerance_or_diet_legacy",
        "diet_legacy",
    }
)
ALLERGEN_CONCEPTS = frozenset(
    {
        "milk_protein",
        "egg",
        "fish",
        "crustacean",
        "mollusc",
        "peanut",
        "tree_nut",
        "soy",
        "wheat",
        "barley",
        "rye",
    }
)
RELATION_TYPES = frozenset({"contains", "may_contain", "cross_contact", "unknown"})
PROVENANCE_STATUSES = frozenset(
    {
        "external_verified",
        "product_label",
        "curated_reviewed",
        "recipe_derived",
        "legacy_inferred",
        "ai_unverified",
        "unknown",
    }
)
VERIFIED_GF_PROVENANCE = frozenset(
    {"external_verified", "product_label", "curated_reviewed"}
)
GLUTEN_CONCEPTS = frozenset({"wheat", "barley", "rye"})

CONCEPT_LABEL_RU = {
    "milk_protein": "белок молока",
    "egg": "яйцо",
    "fish": "рыба",
    "crustacean": "ракообразные",
    "mollusc": "моллюски",
    "peanut": "арахис",
    "tree_nut": "древесные орехи",
    "soy": "соя",
    "wheat": "пшеница",
    "barley": "ячмень",
    "rye": "рожь",
    "lactose_intolerance": "непереносимость лактозы",
    "celiac_disease": "целиакия",
    "gluten_free_diet": "безглютеновая диета",
}

LEGACY_BRIDGES: dict[str, tuple[tuple[str, str], ...]] = {
    "no_peanuts": (("allergy_or_avoidance_legacy", "peanut"),),
    "no_nuts": (
        ("allergy_or_avoidance_legacy", "peanut"),
        ("allergy_or_avoidance_legacy", "tree_nut"),
    ),
    "no_fish": (("allergy_or_avoidance_legacy", "fish"),),
    "no_seafood": (
        ("allergy_or_avoidance_legacy", "fish"),
        ("allergy_or_avoidance_legacy", "crustacean"),
        ("allergy_or_avoidance_legacy", "mollusc"),
    ),
    "no_milk": (("allergy_or_avoidance_legacy", "milk_protein"),),
    "lactose_free": (("intolerance_or_diet_legacy", "lactose_intolerance"),),
    "gluten_free": (("diet_legacy", "gluten_free_diet"),),
}

PROFILE_ALLERGY_ALIASES: dict[str, tuple[str, ...]] = {
    "milk": ("milk_protein",),
    "milk_protein": ("milk_protein",),
    "dairy": ("milk_protein",),
    "eggs": ("egg",),
    "egg": ("egg",),
    "fish": ("fish",),
    "seafood": ("fish", "crustacean", "mollusc"),
    "nuts": ("peanut", "tree_nut"),
    "peanuts": ("peanut",),
    "peanut": ("peanut",),
    "tree_nut": ("tree_nut",),
    "soy": ("soy",),
}

INGREDIENT_CONCEPT_MARKERS: dict[str, tuple[str, ...]] = {
    "milk_protein": (
        "молоко",
        "сливки",
        "сыр",
        "творог",
        "йогурт",
        "кефир",
        "сметана",
        "масло сливочное",
    ),
    "egg": ("яйцо", "яйца", "белок", "желток"),
    "fish": ("рыба", "лосось", "тунец", "треска", "форель", "хек", "минтай"),
    "crustacean": ("креветки", "краб", "раки", "лангуст"),
    "mollusc": ("мидии", "кальмар", "осьминог", "устрицы", "моллюски"),
    "peanut": ("арахис", "арахисовый"),
    "tree_nut": ("орех", "миндаль", "фундук", "кешью", "грецкий орех"),
    "soy": ("соя", "соевый соус", "тофу"),
    "wheat": ("пшеница", "мука пшеничная", "хлеб", "батон", "макароны", "паста", "лаваш"),
    "barley": ("ячмень", "перловка", "крупа перловая"),
    "rye": ("рожь", "ржаной"),
}


@dataclass(frozen=True)
class TypedSafetyEntry:
    kind: str
    concept_id: str
    origin: str
    severity: str = "hard"
    provenance_status: str = "unknown"
    source: str | None = None
    review_status: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in PROFILE_SAFETY_KINDS:
            raise ValueError(f"unsupported profile safety kind: {self.kind}")
        if self.provenance_status not in PROVENANCE_STATUSES:
            raise ValueError(f"unsupported provenance status: {self.provenance_status}")
        if self.kind == "allergy" and self.concept_id == "lactose_intolerance":
            raise ValueError("lactose intolerance must not be stored as allergy")
        if self.kind == "intolerance" and self.concept_id == "milk_protein":
            raise ValueError("milk protein allergy must not be stored as intolerance")
        if self.kind == "medical_condition" and self.concept_id == "gluten_free_diet":
            raise ValueError("gluten-free diet is not a medical condition")

    def to_dict(self) -> dict[str, str | None]:
        return {
            "kind": self.kind,
            "concept_id": self.concept_id,
            "origin": self.origin,
            "severity": self.severity,
            "provenance_status": self.provenance_status,
            "source": self.source,
            "review_status": self.review_status,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class AllergenFact:
    concept_id: str
    relation_type: str
    provenance_status: str
    confidence: str = "medium"
    source_id: str | None = None
    source_record_locator: str | None = None
    ingredient_id: int | None = None
    ingredient_name: str | None = None
    evidence_notes: str | None = None

    def __post_init__(self) -> None:
        if self.concept_id not in ALLERGEN_CONCEPTS:
            raise ValueError(f"unsupported allergen concept: {self.concept_id}")
        if self.relation_type not in RELATION_TYPES:
            raise ValueError(f"unsupported relation type: {self.relation_type}")
        if self.provenance_status not in PROVENANCE_STATUSES:
            raise ValueError(f"unsupported provenance status: {self.provenance_status}")
        if self.provenance_status == "external_verified" and (
            not self.source_id or not self.source_record_locator
        ):
            raise ValueError("external allergen fact requires source and locator")
        if self.provenance_status == "ai_unverified" and self.relation_type == "contains":
            object.__setattr__(self, "confidence", "needs_review")

    def to_dict(self) -> dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "relation_type": self.relation_type,
            "provenance_status": self.provenance_status,
            "confidence": self.confidence,
            "source_id": self.source_id,
            "source_record_locator": self.source_record_locator,
            "ingredient_id": self.ingredient_id,
            "ingredient_name": self.ingredient_name,
            "evidence_notes": self.evidence_notes,
        }


@dataclass(frozen=True)
class CeliacDecision:
    status: GlutenFreeStatus
    reason: str
    provenance_status: str = "unknown"
    matched_concepts: tuple[str, ...] = ()
    review_required: bool = True

    @property
    def safe_for_celiac(self) -> bool:
        return self.status == "verified_gluten_free"


def normalize_typed_safety_entries(values: Iterable[Any] | None) -> list[TypedSafetyEntry]:
    result: list[TypedSafetyEntry] = []
    seen: set[tuple[str, str, str]] = set()
    for raw in values or []:
        if isinstance(raw, TypedSafetyEntry):
            entry = raw
        elif isinstance(raw, dict):
            entry = TypedSafetyEntry(
                kind=str(raw.get("kind") or "").strip(),
                concept_id=str(raw.get("concept_id") or raw.get("concept") or "").strip(),
                origin=str(raw.get("origin") or "user_declared").strip(),
                severity=str(raw.get("severity") or "hard").strip(),
                provenance_status=str(raw.get("provenance_status") or "unknown").strip(),
                source=raw.get("source"),
                review_status=raw.get("review_status"),
                notes=raw.get("notes"),
            )
        else:
            continue
        key = (entry.kind, entry.concept_id, entry.origin)
        if key in seen:
            continue
        seen.add(key)
        result.append(entry)
    return result


def typed_entries_to_dicts(entries: Iterable[TypedSafetyEntry]) -> list[dict[str, str | None]]:
    return [entry.to_dict() for entry in entries]


def legacy_bridge_entries(values: Iterable[str] | None) -> list[TypedSafetyEntry]:
    entries: list[TypedSafetyEntry] = []
    for raw in values or []:
        key = str(raw).strip().lower()
        for kind, concept in LEGACY_BRIDGES.get(key, ()):
            entries.append(
                TypedSafetyEntry(
                    kind=kind,
                    concept_id=concept,
                    origin="legacy_inferred",
                    provenance_status="legacy_inferred",
                    source=key,
                    review_status="needs_review",
                )
            )
    return normalize_typed_safety_entries(entries)


def typed_entries_from_profile(profile: Any) -> list[TypedSafetyEntry]:
    explicit = normalize_typed_safety_entries(getattr(profile, "typed_safety_profile", None))
    if explicit:
        return explicit

    raw_entries: list[TypedSafetyEntry] = []
    for allergy in getattr(profile, "allergies", None) or []:
        key = str(allergy).strip().lower()
        if not key or key == "none":
            continue
        for concept in PROFILE_ALLERGY_ALIASES.get(key, (key,)):
            if concept in ALLERGEN_CONCEPTS:
                raw_entries.append(
                    TypedSafetyEntry(
                        kind="allergy",
                        concept_id=concept,
                        origin="user_declared",
                        provenance_status="unknown",
                        source=key,
                        review_status="unreviewed",
                    )
                )
    raw_entries.extend(legacy_bridge_entries(getattr(profile, "restrictions", None)))
    for diet in getattr(profile, "diets", None) or []:
        if str(diet).strip().lower() == "gluten_free":
            raw_entries.append(
                TypedSafetyEntry(
                    kind="diet",
                    concept_id="gluten_free_diet",
                    origin="user_declared",
                    severity="soft",
                    provenance_status="unknown",
                    source="gluten_free",
                )
            )
    med = str(getattr(profile, "medical_restrictions", "") or "").lower()
    if "celiac" in med or "целиак" in med:
        raw_entries.append(
            TypedSafetyEntry(
                kind="medical_condition",
                concept_id="celiac_disease",
                origin="user_declared",
                provenance_status="unknown",
                source="medical_restrictions",
                review_status="unreviewed",
            )
        )
    return normalize_typed_safety_entries(raw_entries)


def collect_recipe_allergen_facts(recipe: Any) -> list[AllergenFact]:
    explicit = getattr(recipe, "allergen_facts", None)
    if explicit:
        return [
            fact
            if isinstance(fact, AllergenFact)
            else AllergenFact(
                concept_id=str(fact.get("concept_id") or fact.get("concept") or ""),
                relation_type=str(fact.get("relation_type") or "unknown"),
                provenance_status=str(fact.get("provenance_status") or "unknown"),
                confidence=str(fact.get("confidence") or fact.get("review_status") or "medium"),
                source_id=fact.get("source_id"),
                source_record_locator=fact.get("source_record_locator"),
                ingredient_id=fact.get("ingredient_id"),
                ingredient_name=fact.get("ingredient_name"),
                evidence_notes=fact.get("evidence_notes"),
            )
            for fact in explicit
        ]

    rows = getattr(recipe, "allergen_rows", None) or []
    out: list[AllergenFact] = []
    for row in rows:
        concept = getattr(row, "concept_id", None)
        if concept:
            out.append(
                AllergenFact(
                    concept_id=concept,
                    relation_type=getattr(row, "relation_type", None) or "contains",
                    provenance_status=getattr(row, "provenance_status", None)
                    or "legacy_inferred",
                    confidence=getattr(row, "confidence", None) or "medium",
                    source_id=getattr(row, "source_id", None),
                    source_record_locator=getattr(row, "source_record_locator", None),
                    evidence_notes=getattr(row, "evidence_notes", None),
                )
            )
        else:
            legacy = getattr(row, "allergen", None)
            out.extend(_legacy_allergen_facts(str(legacy or "")))
    if out:
        return out

    allergens = list(getattr(recipe, "allergens", None) or [])
    for allergen in allergens:
        out.extend(_legacy_allergen_facts(str(allergen)))
    if out:
        return out

    return derive_allergen_facts_from_ingredients(_collect_ingredient_names(recipe))


def derive_allergen_facts_from_ingredients(names: Iterable[str]) -> list[AllergenFact]:
    out: list[AllergenFact] = []
    seen: set[tuple[str, str, str | None]] = set()
    for name in names:
        text = str(name or "").lower().replace("ё", "е")
        for concept, markers in INGREDIENT_CONCEPT_MARKERS.items():
            if any(marker in text for marker in markers):
                key = (concept, "contains", name)
                if key in seen:
                    continue
                seen.add(key)
                out.append(
                    AllergenFact(
                        concept_id=concept,
                        relation_type="contains",
                        provenance_status="recipe_derived",
                        confidence="medium",
                        ingredient_name=name,
                    )
                )
    return out


def aggregate_allergen_facts(facts: Iterable[AllergenFact]) -> dict[str, dict[str, Any]]:
    order = {"contains": 0, "may_contain": 1, "cross_contact": 2, "unknown": 3}
    out: dict[str, dict[str, Any]] = {}
    for fact in facts:
        current = out.get(fact.concept_id)
        if current is None or order[fact.relation_type] < order[current["relation_type"]]:
            out[fact.concept_id] = {
                "concept_id": fact.concept_id,
                "relation_type": fact.relation_type,
                "provenance_status": fact.provenance_status,
                "confidence": fact.confidence,
                "facts": [fact.to_dict()],
            }
        else:
            current["facts"].append(fact.to_dict())
    return out


def decide_celiac_gluten_free(recipe: Any) -> CeliacDecision:
    status = getattr(recipe, "gluten_free_status", None)
    provenance = getattr(recipe, "gluten_free_provenance_status", None)
    if status == "verified_gluten_free" and provenance in VERIFIED_GF_PROVENANCE:
        return CeliacDecision(
            status="verified_gluten_free",
            reason="structured verified gluten-free provenance",
            provenance_status=provenance,
            review_required=False,
        )

    facts = collect_recipe_allergen_facts(recipe)
    gluten_facts = [fact for fact in facts if fact.concept_id in GLUTEN_CONCEPTS]
    if any(fact.relation_type == "contains" for fact in gluten_facts):
        concepts = tuple(sorted({fact.concept_id for fact in gluten_facts}))
        return CeliacDecision(
            status="not_gluten_free",
            reason="wheat/barley/rye evidence present",
            provenance_status="recipe_derived",
            matched_concepts=concepts,
            review_required=True,
        )
    if any(fact.relation_type == "cross_contact" for fact in gluten_facts):
        concepts = tuple(sorted({fact.concept_id for fact in gluten_facts}))
        return CeliacDecision(
            status="cross_contact_risk",
            reason="gluten cross-contact evidence present",
            provenance_status="recipe_derived",
            matched_concepts=concepts,
            review_required=True,
        )
    return CeliacDecision(
        status="unknown",
        reason="insufficient structured gluten-free provenance",
        provenance_status="unknown",
        review_required=True,
    )


def profile_has_celiac(profile: Any) -> bool:
    return any(
        entry.kind == "medical_condition" and entry.concept_id == "celiac_disease"
        for entry in typed_entries_from_profile(profile)
    )


def lactose_intolerance_conflicts(recipe: Any) -> list[AllergenFact]:
    facts: list[AllergenFact] = []
    for name in _collect_ingredient_names(recipe):
        text = str(name).lower().replace("ё", "е")
        if "безлактоз" in text:
            continue
        if any(marker in text for marker in INGREDIENT_CONCEPT_MARKERS["milk_protein"]):
            facts.append(
                AllergenFact(
                    concept_id="milk_protein",
                    relation_type="contains",
                    provenance_status="recipe_derived",
                    confidence="medium",
                    ingredient_name=name,
                    evidence_notes="lactose-containing dairy candidate",
                )
            )
    return facts


def _legacy_allergen_facts(value: str) -> list[AllergenFact]:
    key = value.strip().lower()
    concepts = PROFILE_ALLERGY_ALIASES.get(key, ())
    return [
        AllergenFact(
            concept_id=concept,
            relation_type="contains",
            provenance_status="legacy_inferred",
            confidence="needs_review",
            evidence_notes=f"legacy allergen row: {value}",
        )
        for concept in concepts
        if concept in ALLERGEN_CONCEPTS
    ]


def _collect_ingredient_names(recipe: Any) -> list[str]:
    ingredients = getattr(recipe, "ingredients", None)
    if isinstance(ingredients, list):
        names: list[str] = []
        for item in ingredients:
            if isinstance(item, dict):
                name = str(item.get("name") or "").strip()
            else:
                name = str(item or "").strip()
            if name:
                names.append(name)
        return names
    rows = getattr(recipe, "ingredient_rows", None) or []
    return [str(getattr(row, "name", "")).strip() for row in rows if getattr(row, "name", "")]
