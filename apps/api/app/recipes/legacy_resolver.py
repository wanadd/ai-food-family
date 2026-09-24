from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LegacyRecipeResolution:
    legacy_recipe_id: int
    status: str
    canonical_recipe_id: str | None = None
    canonical_version_id: str | None = None
    archive_payload: dict[str, Any] | None = None


def resolve_legacy_recipe(
    legacy_recipe_id: int,
    mapping: dict[int, tuple[str, str]] | None,
    archive: dict[int, dict[str, Any]] | None,
) -> LegacyRecipeResolution:
    mapped = (mapping or {}).get(legacy_recipe_id)
    if mapped:
        return LegacyRecipeResolution(legacy_recipe_id, "MAPPED", mapped[0], mapped[1])
    return LegacyRecipeResolution(legacy_recipe_id, "ARCHIVE_FALLBACK", archive_payload=(archive or {}).get(legacy_recipe_id))
