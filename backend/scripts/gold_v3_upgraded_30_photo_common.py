"""Shared helpers for Gold V3 upgraded-30 photo pipeline scripts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCRIPT_VERSION = "gold_v3_upgraded_30_image_urls.v1"
MANIFEST_PATH = Path(__file__).resolve().parents[2] / "data" / "recipe_v2" / "gold_v3_upgraded_30_photo_manifest.json"
EXPECTED_UPGRADE_IDS = [
    2,
    227,
    228,
    229,
    230,
    231,
    232,
    233,
    234,
    235,
    236,
    237,
    238,
    239,
    240,
    241,
    242,
    243,
    244,
    245,
    246,
    247,
    248,
    249,
    250,
    251,
    252,
    253,
    254,
    255,
]
REQUIRED_FILES = ("hero.webp", "card_800.webp", "thumb_400.webp")
IMAGE_URL_FIELDS = ("hero_image_url", "image_url", "thumbnail_url")
FILE_BY_URL_FIELD = {
    "hero_image_url": "hero.webp",
    "image_url": "card_800.webp",
    "thumbnail_url": "thumb_400.webp",
}
EXPECTED_WIDTHS = {
    "hero.webp": (900, 1600),
    "card_800.webp": (600, 1000),
    "thumb_400.webp": (300, 520),
}
MAX_FILE_BYTES = 2_500_000
MIN_FILE_BYTES = 512


def load_manifest(path: Path | None = None) -> dict[str, Any]:
    manifest_path = path or MANIFEST_PATH
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Manifest must be a JSON object")
    return data


def manifest_recipe_ids(manifest: dict[str, Any]) -> list[int]:
    ids = manifest.get("recipe_ids")
    if isinstance(ids, list) and ids:
        return [int(item) for item in ids]
    recipes = manifest.get("recipes") or []
    return sorted(int(recipe["id"]) for recipe in recipes if isinstance(recipe, dict) and recipe.get("id") is not None)


def manifest_hash(manifest: dict[str, Any]) -> str:
    payload = {
        "recipe_ids": manifest_recipe_ids(manifest),
        "recipes": [
            {
                "id": recipe.get("id"),
                "public_urls": recipe.get("public_urls"),
            }
            for recipe in manifest.get("recipes") or []
            if isinstance(recipe, dict)
        ],
        "schema_version": manifest.get("schema_version"),
    }
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:16]


def plan_id_for(manifest: dict[str, Any], *, script_version: str = SCRIPT_VERSION) -> str:
    payload = {
        "recipe_ids": manifest_recipe_ids(manifest),
        "manifest_hash": manifest_hash(manifest),
        "script_version": script_version,
        "target_urls": {
            str(recipe.get("id")): recipe.get("public_urls")
            for recipe in manifest.get("recipes") or []
            if isinstance(recipe, dict)
        },
    }
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return f"gold-v3-image-urls-{digest[:16]}"


def recipe_manifest_by_id(manifest: dict[str, Any]) -> dict[int, dict[str, Any]]:
    rows: dict[int, dict[str, Any]] = {}
    for recipe in manifest.get("recipes") or []:
        if not isinstance(recipe, dict) or recipe.get("id") is None:
            continue
        rows[int(recipe["id"])] = recipe
    return rows


def expected_public_urls(recipe_id: int, manifest_recipe: dict[str, Any] | None = None) -> dict[str, str]:
    if manifest_recipe and isinstance(manifest_recipe.get("public_urls"), dict):
        return {key: str(value) for key, value in manifest_recipe["public_urls"].items()}
    base = f"/recipe-images/{recipe_id}"
    return {
        "hero_image_url": f"{base}/hero.webp",
        "image_url": f"{base}/card_800.webp",
        "thumbnail_url": f"{base}/thumb_400.webp",
    }


def validate_manifest_ids(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    ids = manifest_recipe_ids(manifest)
    if ids != EXPECTED_UPGRADE_IDS:
        errors.append(f"manifest recipe_ids must be {EXPECTED_UPGRADE_IDS}, got {ids}")
    if int(manifest.get("recipe_count") or len(ids)) != 30:
        errors.append("manifest recipe_count must be 30")
    return errors
