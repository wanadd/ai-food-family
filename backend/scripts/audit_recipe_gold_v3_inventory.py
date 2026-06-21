#!/usr/bin/env python3
"""Read-only Recipe Gold V3 local artifact, image, and batch inventory."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
INVENTORY_MD = REPORTS / "SPRINT_1_3A_RECIPE_GOLD_V3_INVENTORY.md"
INVENTORY_JSON = REPORTS / "SPRINT_1_3A_RECIPE_GOLD_V3_INVENTORY.json"
IMAGE_MD = REPORTS / "SPRINT_1_3A_RECIPE_GOLD_V3_IMAGE_INVENTORY.md"
IMAGE_JSON = REPORTS / "SPRINT_1_3A_RECIPE_GOLD_V3_IMAGE_INVENTORY.json"
COMPARE_MD = REPORTS / "SPRINT_1_3A_RECIPE_GOLD_V3_BATCH_COMPARISON.md"
COMPARE_JSON = REPORTS / "SPRINT_1_3A_RECIPE_GOLD_V3_BATCH_COMPARISON.json"
DECISION_MD = REPORTS / "SPRINT_1_3A_RECIPE_GOLD_V3_DECISION_REPORT.md"
DB_STATE_JSON = REPORTS / "SPRINT_1_3A_RECIPE_GOLD_V3_DB_STATE.json"

BATCH_PATTERNS = [
    "exports/*recipe_gold_v3*.jsonl",
    "data/recipe_v2/gold_recipes_30.jsonl",
]

FILE_PATTERNS = {
    "api_gold_v3_modules": ["apps/api/app/recipes/recipe_gold_v3_*.py"],
    "backend_gold_v3_scripts": ["backend/scripts/*recipe_gold_v3*.py"],
    "api_gold_v3_tests": ["apps/api/tests/test_recipe_gold_v3_*.py"],
    "gold_v3_exports": ["exports/*recipe_gold_v3*.jsonl"],
    "gold_recipes_30": ["data/recipe_v2/gold_recipes_30.jsonl"],
    "gold_v3_reports": ["reports/recipe_gold_v3*.md", "reports/recipe_gold_v3_stage_r_created_ids.json"],
    "web_recipe_images": ["apps/web/public/recipe-images/**"],
}

IMAGE_ROOTS = [
    ROOT / "apps/web/public/recipe-images",
    ROOT / "apps/api/public/recipe-images",
    ROOT / "backend/public/recipe-images",
    ROOT / "public/recipe-images",
    Path("/var/www/ai-food-family/apps/web/public/recipe-images"),
    Path("/var/www/ai-food-family/apps/api/public/recipe-images"),
    Path("/var/www/ai-food-family-data/recipe-images"),
    Path("/app/public/recipe-images"),
    Path("/app/apps/web/public/recipe-images"),
]

REQUIRED_IMAGE_FILES = ("hero.webp", "card_800.webp", "thumb_400.webp")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_text(path: Path, limit: int = 200_000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""
    return text[:limit]


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line_no, line in enumerate(fh, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                data = json.loads(stripped)
            except json.JSONDecodeError as exc:
                rows.append({"_line": line_no, "_invalid_json": str(exc)})
                continue
            if isinstance(data, dict):
                data["_line"] = line_no
                rows.append(data)
            else:
                rows.append({"_line": line_no, "_invalid_json": "not an object"})
    return rows


def norm_title(title: str) -> str:
    text = (title or "").casefold().replace("ё", "е")
    text = re.sub(r"[^0-9a-zа-я]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def collect_files() -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for group, patterns in FILE_PATTERNS.items():
        found: dict[Path, dict[str, Any]] = {}
        for pattern in patterns:
            for path in ROOT.glob(pattern):
                if path.is_dir():
                    continue
                found[path] = {
                    "path": rel(path),
                    "exists": path.exists(),
                    "bytes": path.stat().st_size if path.exists() else 0,
                    "mtime": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
                    if path.exists()
                    else None,
                }
        out[group] = sorted(found.values(), key=lambda item: item["path"])
    return out


def summarize_batch(path: Path) -> dict[str, Any]:
    rows = load_jsonl(path)
    valid_json = [r for r in rows if "_invalid_json" not in r]
    invalid_json = [r for r in rows if "_invalid_json" in r]
    scores = [
        int((r.get("quality") or {}).get("score"))
        for r in valid_json
        if isinstance((r.get("quality") or {}).get("score"), int)
    ]
    titles = [str(r.get("title") or "") for r in valid_json]
    meal_counts = Counter(str(r.get("meal_type") or "missing") for r in valid_json)
    schema_counts = Counter(str(r.get("schema_version") or "missing") for r in valid_json)
    source_counts = Counter(str(r.get("source_type") or "missing") for r in valid_json)
    duplicate_titles = [
        title for title, count in Counter(norm_title(t) for t in titles if t).items() if count > 1
    ]
    return {
        "path": rel(path),
        "exists": path.exists(),
        "records": len(rows),
        "valid_json_records": len(valid_json),
        "invalid_json_records": len(invalid_json),
        "schema_versions": dict(schema_counts),
        "source_types": dict(source_counts),
        "meal_types": dict(meal_counts),
        "avg_score": round(sum(scores) / len(scores), 2) if scores else None,
        "min_score": min(scores) if scores else None,
        "max_score": max(scores) if scores else None,
        "duplicate_normalized_titles": duplicate_titles,
        "titles": titles,
    }


def parse_reports() -> dict[str, Any]:
    reports = sorted(REPORTS.glob("recipe_gold_v3*"))
    parsed: dict[str, Any] = {}
    for path in reports:
        item: dict[str, Any] = {
            "path": rel(path),
            "bytes": path.stat().st_size,
            "mtime": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
        }
        if path.suffix.lower() == ".json":
            data = load_json(path)
            item["json_type"] = type(data).__name__
            if isinstance(data, list):
                item["records"] = len(data)
                item["created_ids"] = data
            elif isinstance(data, dict):
                item["keys"] = sorted(data.keys())
                for key in ("created", "created_ids", "ids", "recipe_ids"):
                    if isinstance(data.get(key), list):
                        item["created_ids"] = [
                            entry.get("id") if isinstance(entry, dict) else entry
                            for entry in data[key]
                        ]
                item["records"] = data.get("records") or data.get("record_count")
        else:
            text = read_text(path)
            lower = text.lower()
            item["records"] = first_number(text, [r"records?\s*[:`* ]+(\d+)", r"record_count\s*[:`* ]+(\d+)"])
            item["valid"] = first_number(text, [r"valid\s*[:`* ]+(\d+)", r"valid_records\s*[:`* ]+(\d+)"])
            item["invalid"] = first_number(text, [r"invalid\s*[:`* ]+(\d+)", r"invalid_records\s*[:`* ]+(\d+)"])
            item["avg_score"] = first_float(text, [r"avg(?:erage)? score\s*[:`* ]+([0-9.]+)", r"avg_score\s*[:`* ]+([0-9.]+)"])
            item["min_score"] = first_float(text, [r"min score\s*[:`* ]+([0-9.]+)", r"min_score\s*[:`* ]+([0-9.]+)"])
            item["quality_gate"] = "PASS" if "pass" in lower else ("FAIL" if "fail" in lower else None)
            item["mentions_image_url"] = any(k in lower for k in ("hero_image_url", "image_url", "thumbnail_url", "/recipe-images"))
            item["mentions_created_ids"] = "created" in lower and "id" in lower
        parsed[path.name] = item
    return parsed


def first_number(text: str, patterns: list[str]) -> int | None:
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.I)
        if m:
            return int(m.group(1))
    return None


def first_float(text: str, patterns: list[str]) -> float | None:
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.I)
        if m:
            return float(m.group(1))
    return None


def created_ids() -> list[int]:
    data = load_json(REPORTS / "recipe_gold_v3_stage_r_created_ids.json")
    ids: list[int] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, int):
                ids.append(item)
            elif isinstance(item, dict) and isinstance(item.get("id"), int):
                ids.append(item["id"])
    elif isinstance(data, dict):
        for key in ("created", "created_ids", "ids", "recipe_ids"):
            value = data.get(key)
            if isinstance(value, list):
                for item in value:
                    raw_id = item.get("id") if isinstance(item, dict) else item
                    if isinstance(raw_id, int) or str(raw_id).isdigit():
                        ids.append(int(raw_id))
    return sorted(set(ids))


def collect_image_files() -> dict[str, Any]:
    roots: list[dict[str, Any]] = []
    for root in IMAGE_ROOTS:
        exists = root.exists()
        files = []
        if exists:
            files = [
                {"path": rel(path), "bytes": path.stat().st_size}
                for path in sorted(root.rglob("*"))
                if path.is_file()
            ]
        roots.append({"path": rel(root), "exists": exists, "file_count": len(files), "files": files[:500]})
    return {"roots": roots}


def extract_report_image_urls() -> list[str]:
    urls: set[str] = set()
    for path in REPORTS.glob("recipe_gold_v3*.md"):
        text = read_text(path)
        for match in re.findall(r"(?:hero_image_url|image_url|thumbnail_url)\s*[:=` ]+([^\s)`]+)", text):
            urls.add(match.strip("`'\""))
        for match in re.findall(r"(/recipe-images/[^\s)`]+)", text):
            urls.add(match.strip("`'\""))
    return sorted(urls)


def batch_records_by_title(batch_summaries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for batch in batch_summaries:
        path = ROOT / batch["path"]
        for row in load_jsonl(path):
            title = str(row.get("title") or "")
            if not title:
                continue
            out[norm_title(title)].append(
                {
                    "batch": batch["path"],
                    "title": title,
                    "meal_type": row.get("meal_type"),
                    "score": (row.get("quality") or {}).get("score"),
                    "main_ingredient": ((row.get("ingredients") or [{}])[0] or {}).get("name")
                    if isinstance(row.get("ingredients"), list)
                    else None,
                    "has_image_prompt_data": bool(row.get("image_prompt_data")),
                    "schema_version": row.get("schema_version"),
                }
            )
    return out


def load_db_state() -> dict[str, Any] | None:
    data = load_json(DB_STATE_JSON)
    return data if isinstance(data, dict) else None


def build_batch_comparison(batch_summaries: list[dict[str, Any]], image_urls: list[str]) -> dict[str, Any]:
    db = load_db_state()
    db_by_title = {}
    if db:
        for recipe in db.get("gold_v3_recipes") or []:
            db_by_title[norm_title(recipe.get("title") or "")] = recipe
    comparison = []
    for key, records in sorted(batch_records_by_title(batch_summaries).items()):
        imported = key in db_by_title
        has_image = imported and bool(
            db_by_title[key].get("hero_image_url")
            or db_by_title[key].get("image_url")
            or db_by_title[key].get("thumbnail_url")
        )
        duplicate_risk = len(records) > 1 or imported
        comparison.append(
            {
                "normalized_title": key,
                "titles": sorted({r["title"] for r in records}),
                "batches": sorted({r["batch"] for r in records}),
                "duplicate_risk": duplicate_risk,
                "scores": [r["score"] for r in records if r.get("score") is not None],
                "meal_types": sorted({str(r.get("meal_type")) for r in records if r.get("meal_type")}),
                "main_ingredients": sorted({str(r.get("main_ingredient")) for r in records if r.get("main_ingredient")}),
                "already_imported": imported,
                "db_id": db_by_title.get(key, {}).get("id"),
                "has_image": has_image,
                "can_be_reused": True,
                "needs_repair": any(r.get("schema_version") != "recipe_gold_v3" for r in records),
                "should_be_preserved": imported or any("generated_10" in r["batch"] for r in records),
                "should_be_excluded": False,
            }
        )
    return {
        "generated_at": now(),
        "db_state_loaded": bool(db),
        "report_image_urls_count": len(image_urls),
        "recipes": comparison,
        "summary": {
            "unique_normalized_titles": len(comparison),
            "already_imported": sum(1 for r in comparison if r["already_imported"]),
            "duplicate_risk": sum(1 for r in comparison if r["duplicate_risk"]),
            "has_image": sum(1 for r in comparison if r["has_image"]),
        },
    }


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def md_table(rows: list[list[Any]], headers: list[str]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("\n", " ") for cell in row) + " |")
    return "\n".join(lines)


def render_inventory(data: dict[str, Any]) -> str:
    batch_rows = [
        [
            b["path"],
            b["records"],
            b["valid_json_records"],
            b["invalid_json_records"],
            b["avg_score"],
            b["min_score"],
            ", ".join(f"{k}:{v}" for k, v in b["meal_types"].items()),
        ]
        for b in data["batches"]
    ]
    report_rows = []
    for name, item in data["parsed_reports"].items():
        report_rows.append(
            [
                name,
                item.get("records"),
                item.get("valid"),
                item.get("invalid"),
                item.get("avg_score"),
                item.get("min_score"),
                item.get("quality_gate"),
                item.get("mentions_image_url"),
            ]
        )
    gaps = data["gaps"]
    lines = [
        "# Sprint 1.3A Recipe Gold V3 Inventory",
        "",
        f"Generated: `{data['generated_at']}`",
        "",
        "## Batch Files",
        "",
        f"- Gold V3 batch files found: `{len(data['batches'])}`",
        "",
        md_table(batch_rows, ["path", "records", "valid_json", "invalid_json", "avg_score", "min_score", "meal_types"]),
        "",
        "## Reports Parsed",
        "",
        md_table(report_rows, ["report", "records", "valid", "invalid", "avg", "min", "gate", "image_urls"]),
        "",
        "## Created IDs",
        "",
        f"- Created IDs from Stage R report: `{data['created_ids']}`",
        "",
        "## Images",
        "",
        f"- Image URLs mentioned in reports: `{len(data['report_image_urls'])}`",
        f"- Local repo image files: `{sum(root['file_count'] for root in data['image_files']['roots'] if not str(root['path']).startswith('/'))}`",
        "",
        "## Gaps",
        "",
        *[f"- {gap}" for gap in gaps],
    ]
    return "\n".join(lines) + "\n"


def render_image_inventory(data: dict[str, Any]) -> str:
    rows = [[root["path"], root["exists"], root["file_count"]] for root in data["roots"]]
    return "\n".join(
        [
            "# Sprint 1.3A Recipe Gold V3 Image Inventory",
            "",
            f"Generated: `{data['generated_at']}`",
            "",
            md_table(rows, ["path", "exists", "file_count"]),
            "",
            f"- Report image URLs: `{len(data['report_image_urls'])}`",
            f"- DB URLs loaded: `{data['db_urls_loaded']}`",
            f"- Gold V3 DB recipes with any image URL: `{data['db_gold_v3_with_any_image']}`",
            "",
            "## Required Files",
            "",
            f"- Required per recipe: `{', '.join(REQUIRED_IMAGE_FILES)}`",
            f"- Local required-file complete recipes: `{data['local_required_complete']}`",
            "",
        ]
    )


def render_comparison(data: dict[str, Any]) -> str:
    rows = [
        [
            r["normalized_title"],
            ", ".join(r["batches"]),
            r["already_imported"],
            r.get("db_id"),
            r["duplicate_risk"],
            r["has_image"],
            r["needs_repair"],
        ]
        for r in data["recipes"][:80]
    ]
    return "\n".join(
        [
            "# Sprint 1.3A Recipe Gold V3 Batch Comparison",
            "",
            f"Generated: `{data['generated_at']}`",
            "",
            md_table(rows, ["title_key", "batches", "imported", "db_id", "dup_risk", "has_image", "needs_repair"]),
            "",
            "## Summary",
            "",
            *[f"- {k}: `{v}`" for k, v in data["summary"].items()],
            "",
        ]
    )


def render_decision(inventory: dict[str, Any], image: dict[str, Any], comparison: dict[str, Any]) -> str:
    pilot_batches = [b for b in inventory["batches"] if "generated_10" in b["path"]]
    gold30 = next((b for b in inventory["batches"] if b["path"].endswith("gold_recipes_30.jsonl")), None)
    db = load_db_state() or {}
    created = inventory["created_ids"]
    created_existing = db.get("created_ids_existing") or []
    imported_count = len(db.get("gold_v3_recipes") or [])
    image_count = image.get("db_gold_v3_with_any_image", 0)
    if imported_count >= 10 and image_count >= 10:
        path = "A. preserve 10, then validate/import or repair 30 and connect UI/Menu."
    elif imported_count >= 10:
        path = "B. preserve 10, repair/sync photos, then decide/import 30."
    elif pilot_batches:
        path = "C. 10 are present as dry-run/batch artifacts; run quality gate then safe import 10."
    elif gold30 and gold30.get("valid_json_records"):
        path = "E. repair/validate batch before import."
    else:
        path = "Inventory incomplete; do not generate more until DB/image state is confirmed."
    lines = [
        "# Sprint 1.3A Recipe Gold V3 Decision Report",
        "",
        f"Generated: `{now()}`",
        "",
        "## Existing Pilot",
        "",
        f"- 10 Gold V3 pilot batch files present: `{bool(pilot_batches)}`",
        f"- imported Gold V3 DB recipes: `{imported_count}`",
        f"- created IDs from Stage R: `{created}`",
        f"- created IDs existing in DB: `{created_existing}`",
        f"- DB recipes with any image URL: `{image_count}`",
        "- Decision: preserve existing pilot artifacts and any imported DB rows; do not regenerate blindly.",
        "",
        "## Gold Recipes 30",
        "",
        f"- file exists: `{bool(gold30 and gold30.get('exists'))}`",
        f"- records: `{gold30.get('records') if gold30 else None}`",
        f"- valid JSON records: `{gold30.get('valid_json_records') if gold30 else None}`",
        f"- avg score in file: `{gold30.get('avg_score') if gold30 else None}`",
        "- Needs validator/quality gate before import: `yes` unless latest quality report explicitly covers this exact batch.",
        "",
        "## Images",
        "",
        f"- local repo image roots with files: `{sum(1 for r in image['roots'] if r['file_count'])}`",
        f"- report image URLs found: `{len(inventory['report_image_urls'])}`",
        f"- need sync: `{image_count == 0}`",
        f"- need generation: `unknown`; sync/check server paths first.",
        "",
        "## Next Implementation Plan",
        "",
        f"Recommended path: **{path}**",
        "",
        "Do not import, generate, or overwrite images until this decision is reviewed.",
    ]
    return "\n".join(lines) + "\n"


def build_inventory() -> dict[str, Any]:
    files = collect_files()
    batch_paths = []
    for pattern in BATCH_PATTERNS:
        batch_paths.extend(ROOT.glob(pattern))
    batches = [summarize_batch(path) for path in sorted(set(batch_paths))]
    parsed_reports = parse_reports()
    ids = created_ids()
    image_files = collect_image_files()
    report_image_urls = extract_report_image_urls()
    gaps = []
    if not ids:
        gaps.append("No created recipe IDs parsed from reports/recipe_gold_v3_stage_r_created_ids.json.")
    local_web = next((r for r in image_files["roots"] if r["path"] == "apps/web/public/recipe-images"), None)
    if local_web and local_web["file_count"] <= 1:
        gaps.append("Local apps/web/public/recipe-images has no real recipe image files.")
    if not report_image_urls:
        gaps.append("No image URLs parsed from Gold V3 reports.")
    if not (ROOT / "data/recipe_v2/gold_recipes_30.jsonl").exists():
        gaps.append("data/recipe_v2/gold_recipes_30.jsonl missing.")
    return {
        "generated_at": now(),
        "files": files,
        "batches": batches,
        "parsed_reports": parsed_reports,
        "created_ids": ids,
        "image_files": image_files,
        "report_image_urls": report_image_urls,
        "gaps": gaps,
    }


def build_image_inventory(inventory: dict[str, Any]) -> dict[str, Any]:
    image_files = inventory["image_files"]
    db = load_db_state()
    db_recipes = db.get("gold_v3_recipes", []) if db else []
    local_complete = 0
    for recipe in db_recipes:
        rid = str(recipe.get("id"))
        for root in IMAGE_ROOTS:
            if all((root / rid / name).exists() for name in REQUIRED_IMAGE_FILES):
                local_complete += 1
                break
    data = {
        "generated_at": now(),
        **image_files,
        "report_image_urls": inventory["report_image_urls"],
        "db_urls_loaded": bool(db),
        "db_gold_v3_with_any_image": sum(
            1
            for r in db_recipes
            if r.get("hero_image_url") or r.get("image_url") or r.get("thumbnail_url")
        ),
        "local_required_complete": local_complete,
        "required_files": list(REQUIRED_IMAGE_FILES),
        "note": "Server/VPS paths are checked only when this script runs on that host/container; no SSH is attempted.",
    }
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--images-only", action="store_true")
    args = parser.parse_args()
    REPORTS.mkdir(exist_ok=True)
    inventory = build_inventory()
    image_inventory = build_image_inventory(inventory)
    if not args.images_only:
        comparison = build_batch_comparison(inventory["batches"], inventory["report_image_urls"])
        write_json(INVENTORY_JSON, inventory)
        INVENTORY_MD.write_text(render_inventory(inventory), encoding="utf-8")
        write_json(COMPARE_JSON, comparison)
        COMPARE_MD.write_text(render_comparison(comparison), encoding="utf-8")
        DECISION_MD.write_text(render_decision(inventory, image_inventory, comparison), encoding="utf-8")
    write_json(IMAGE_JSON, image_inventory)
    IMAGE_MD.write_text(render_image_inventory(image_inventory), encoding="utf-8")
    print(f"Wrote {INVENTORY_MD if not args.images_only else IMAGE_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
