from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
EXPECTED_IDS = [2, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255]
MANIFEST_PATH = ROOT / "data" / "recipe_v2" / "gold_v3_upgraded_30_photo_manifest.json"
REQUIRED_FILES = ("hero.webp", "card_800.webp", "thumb_400.webp")
WIDTHS = {"hero.webp": 1200, "card_800.webp": 800, "thumb_400.webp": 400}


def _load_script(name: str):
    if name in sys.modules:
        return sys.modules[name]
    path = ROOT / "backend" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


MIN_PLACEHOLDER_BYTES = 1024


def _write_webp(path: Path, width: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Minimal placeholder bytes; validator dimensions are mocked in tests when Pillow is absent.
    path.write_bytes(b"\x00" * max(MIN_PLACEHOLDER_BYTES, width))


def _fake_inspect_image_file(path: Path) -> dict:
    validate = _load_script("validate_gold_v3_upgraded_30_images")
    width = WIDTHS.get(path.name, 800)
    if not path.is_file():
        return {
            "path": str(path),
            "exists": False,
            "size_bytes": None,
            "format": None,
            "width": None,
            "height": None,
            "ok": False,
            "issues": ["missing_file"],
        }
    size = path.stat().st_size
    issues = []
    if size < validate.MIN_FILE_BYTES:
        issues.append("file_too_small")
    if path.suffix.lower() != ".webp":
        issues.append("not_webp")
    min_w, max_w = validate.EXPECTED_WIDTHS.get(path.name, (1, 10_000))
    if width < min_w or width > max_w:
        issues.append(f"width_out_of_range:{width}")
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": size,
        "format": "WEBP",
        "width": width,
        "height": int(width * 0.75),
        "ok": not issues,
        "issues": issues,
    }


@pytest.fixture(autouse=True)
def _mock_image_inspection(monkeypatch: pytest.MonkeyPatch):
    validate = _load_script("validate_gold_v3_upgraded_30_images")
    monkeypatch.setattr(validate, "inspect_image_file", _fake_inspect_image_file)


def _populate_image_root(root: Path, recipe_ids: list[int] | None = None) -> None:
    for recipe_id in recipe_ids or EXPECTED_IDS:
        for filename in REQUIRED_FILES:
            _write_webp(root / str(recipe_id) / filename, WIDTHS[filename])


def test_manifest_contains_exactly_expected_ids():
    manifest = _load_manifest()
    assert manifest["recipe_count"] == 30
    assert manifest["recipe_ids"] == EXPECTED_IDS
    assert sorted(recipe["id"] for recipe in manifest["recipes"]) == EXPECTED_IDS


def test_validator_catches_missing_hero_card_thumb(tmp_path: Path):
    validate = _load_script("validate_gold_v3_upgraded_30_images")
    manifest = _load_manifest()
    report = validate.validate(
        manifest=manifest,
        image_root=tmp_path,
        public_base_url=None,
        public_timeout=1.0,
        strict_extra_ids=False,
    )
    assert report["missing_asset_count"] == 30
    assert report["complete_triplets"] == 0
    assert report["ok"] is False


def test_validator_accepts_complete_webp_triplets(tmp_path: Path):
    validate = _load_script("validate_gold_v3_upgraded_30_images")
    _populate_image_root(tmp_path)
    manifest = _load_manifest()
    report = validate.validate(
        manifest=manifest,
        image_root=tmp_path,
        public_base_url=None,
        public_timeout=1.0,
        strict_extra_ids=False,
    )
    assert report["complete_triplets"] == 30
    assert report["missing_asset_count"] == 0
    assert report["ok"] is True


def test_dry_run_does_not_mutate_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    apply_mod = _load_script("apply_gold_v3_upgraded_30_image_urls")
    _populate_image_root(tmp_path)

    def _fail_db(*_args, **_kwargs):
        raise AssertionError("DB should not be queried during dry-run apply path")

    monkeypatch.setattr(apply_mod, "execute_apply", _fail_db)
    report = apply_mod.build_report(
        apply=False,
        manifest_path=MANIFEST_PATH,
        image_root=tmp_path,
        public_base_url=None,
        confirm_plan_id=None,
    )
    assert report["db_writes"] == 0
    assert report["apply_executed"] is False
    assert report["mode"] == "dry-run"


def test_apply_refuses_without_env_guard(tmp_path: Path):
    apply_mod = _load_script("apply_gold_v3_upgraded_30_image_urls")
    _populate_image_root(tmp_path)
    report = apply_mod.build_report(
        apply=True,
        manifest_path=MANIFEST_PATH,
        image_root=tmp_path,
        public_base_url=None,
        confirm_plan_id=apply_mod.plan_id_for(_load_manifest()),
    )
    assert "missing_env:PLANAM_ALLOW_GOLD_V3_IMAGE_URL_APPLY=YES" in report["safety_guards"]["guard_blockers"]


def test_apply_refuses_without_confirm_plan_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    apply_mod = _load_script("apply_gold_v3_upgraded_30_image_urls")
    _populate_image_root(tmp_path)
    monkeypatch.setenv("PLANAM_ALLOW_GOLD_V3_IMAGE_URL_APPLY", "YES")
    report = apply_mod.build_report(
        apply=True,
        manifest_path=MANIFEST_PATH,
        image_root=tmp_path,
        public_base_url=None,
        confirm_plan_id=None,
    )
    assert "missing_confirm_plan_id" in report["safety_guards"]["guard_blockers"]


def test_apply_refuses_if_image_assets_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    apply_mod = _load_script("apply_gold_v3_upgraded_30_image_urls")
    monkeypatch.setenv("PLANAM_ALLOW_GOLD_V3_IMAGE_URL_APPLY", "YES")
    manifest = _load_manifest()
    report = apply_mod.build_report(
        apply=True,
        manifest_path=MANIFEST_PATH,
        image_root=tmp_path,
        public_base_url=None,
        confirm_plan_id=apply_mod.plan_id_for(manifest),
    )
    assert "missing_assets" in report["safety_guards"]["guard_blockers"]


def test_apply_updates_only_image_url_fields(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    apply_mod = _load_script("apply_gold_v3_upgraded_30_image_urls")
    _populate_image_root(tmp_path)
    monkeypatch.setenv("PLANAM_ALLOW_GOLD_V3_IMAGE_URL_APPLY", "YES")
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    manifest = _load_manifest()

    class FakeResult:
        rowcount = 1

    class FakeConn:
        def __init__(self) -> None:
            self.executed: list[tuple[str, dict | None]] = []

        def execute(self, query, params=None):
            self.executed.append((str(query), params))
            return FakeResult()

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class FakeEngine:
        def __init__(self) -> None:
            self.conn = FakeConn()

        def begin(self):
            return self.conn

    fake_engine = FakeEngine()

    def _fake_create_engine(_url, **_kwargs):
        return fake_engine

    def _fake_inspect(_database_url: str):
        return {
            "recipe_count": 265,
            "max_recipe_id": 265,
            "rows_by_id": {
                recipe_id: {
                    "id": recipe_id,
                    "hero_image_url": None,
                    "image_url": None,
                    "thumbnail_url": None,
                }
                for recipe_id in EXPECTED_IDS
            },
        }

    def _fake_text(sql: str) -> str:
        return sql

    monkeypatch.setattr(apply_mod, "import_sqlalchemy", lambda: (_fake_create_engine, _fake_text))
    monkeypatch.setattr(apply_mod, "inspect_db_state", _fake_inspect)

    report = apply_mod.build_report(
        apply=True,
        manifest_path=MANIFEST_PATH,
        image_root=tmp_path,
        public_base_url=None,
        confirm_plan_id=apply_mod.plan_id_for(manifest),
    )
    result = apply_mod.execute_apply(report)

    assert result["apply_executed"] is True
    assert result["db_writes"] == 30
    sql, params = fake_engine.conn.executed[0]
    assert "hero_image_url" in sql
    assert "image_url" in sql
    assert "thumbnail_url" in sql
    assert "ingredients" not in sql.lower()
    assert "steps" not in sql.lower()
    assert params["hero_image_url"] == "/recipe-images/2/hero.webp"
    assert params["image_url"] == "/recipe-images/2/card_800.webp"
    assert params["thumbnail_url"] == "/recipe-images/2/thumb_400.webp"


def test_apply_refuses_unexpected_recipe_ids(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    apply_mod = _load_script("apply_gold_v3_upgraded_30_image_urls")
    _populate_image_root(tmp_path)
    monkeypatch.setenv("PLANAM_ALLOW_GOLD_V3_IMAGE_URL_APPLY", "YES")
    manifest = _load_manifest()
    report = apply_mod.build_report(
        apply=True,
        manifest_path=MANIFEST_PATH,
        image_root=tmp_path,
        public_base_url=None,
        confirm_plan_id=apply_mod.plan_id_for(manifest),
        unexpected_recipe_ids=[999],
    )
    assert "unexpected_recipe_ids:[999]" in report["safety_guards"]["guard_blockers"]


def test_plan_id_is_deterministic():
    common = _load_script("gold_v3_upgraded_30_photo_common")
    manifest = _load_manifest()
    first = common.plan_id_for(manifest)
    second = common.plan_id_for(manifest)
    assert first == second
    assert first.startswith("gold-v3-image-urls-")
