"""Tests for Gold V3 recipe image pipeline (Stage IMG)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.recipes.image_generation_config import (
    DEFAULT_ALLOWLIST_IDS,
    ESTIMATED_COST_PER_IMAGE_USD,
    IMAGE_API_KEY_ENV_NAME,
    api_key_status,
    get_settings,
    validate_max_cost_usd,
)
from app.recipes.recipe_gold_v3_image_pipeline import (
    IdNotAllowedError,
    build_master_prompt,
    build_public_image_urls,
    check_apply_guards,
    derivatives_complete,
    has_existing_hero,
    infer_dish_type,
    load_created_ids_from_report,
    plan_image_generation,
    validate_ids_allowed,
)


def _recipe(
    *,
    rid: int,
    title: str,
    hero_url: str | None = None,
    source_type: str = "import",
    tags: list | None = None,
):
    return SimpleNamespace(
        id=rid,
        title=title,
        meal_type="dinner",
        category="main",
        source_type=source_type,
        tags=tags if tags is not None else ["gold_v3"],
        hero_image_url=hero_url,
        image_url=None,
        thumbnail_url=None,
        ingredients=[{"name": "курица"}, {"name": "морковь"}],
    )


def test_config_defaults():
    settings = get_settings(dry_run=True)
    assert settings.provider == "openai"
    assert settings.model == "gpt-image-1"
    assert settings.api_key_env_name == IMAGE_API_KEY_ENV_NAME
    assert settings.dry_run is True
    assert settings.generation_enabled is False


def test_api_key_status_never_returns_secret(monkeypatch):
    monkeypatch.delenv("PLANAM_IMAGE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    status = api_key_status()
    assert status["configured"] is False
    assert "sk-" not in str(status)

    monkeypatch.setenv("PLANAM_IMAGE_OPENAI_API_KEY", "sk-secret-value")
    status = api_key_status()
    assert status["configured"] is True
    assert status["env_name"] == IMAGE_API_KEY_ENV_NAME
    assert "sk-secret" not in str(status)


def test_validate_max_cost_usd():
    assert validate_max_cost_usd(0.63, None)[0] is False
    assert validate_max_cost_usd(0.63, 0.50)[0] is False
    assert validate_max_cost_usd(0.63, 1.0)[0] is True


def test_validate_ids_outside_allowlist_without_explicit():
    with pytest.raises(IdNotAllowedError):
        validate_ids_allowed([999], explicit_ids=False)


def test_validate_ids_explicit_override():
    validate_ids_allowed([999], explicit_ids=True)


def test_load_created_ids_from_report(tmp_path: Path):
    report = tmp_path / "created.json"
    report.write_text(
        '{"created": [{"id": 256, "title": "A"}, {"id": 265, "title": "B"}]}\n',
        encoding="utf-8",
    )
    assert load_created_ids_from_report(report) == [256, 265]


def test_build_master_prompt_contains_dish_title():
    prompt = build_master_prompt(
        {
            "title": "Куриный суп с овощами",
            "meal_type": "lunch",
            "category": "soup",
            "ingredients": [{"name": "курица"}],
        }
    )
    assert "Куриный суп с овощами" in prompt
    assert "deep ceramic bowl" in prompt


def test_infer_dish_type_soup_and_cutlet():
    assert infer_dish_type("Куриный суп с овощами", "lunch", "soup") == "soup"
    assert infer_dish_type("Котлеты с овощами", "dinner", "main") == "cutlet"


def test_plan_would_generate_when_no_hero(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.recipes.recipe_gold_v3_image_pipeline.fetch_gold_v3_recipes_by_ids",
        lambda _s, ids: {256: _recipe(rid=256, title="Котлеты с овощами")},
    )
    plan = plan_image_generation(MagicMock(), [256], images_dir=tmp_path, explicit_ids=True)
    assert plan["ok"] is True
    assert plan["to_generate_count"] == 1
    assert plan["to_skip_count"] == 0


def test_plan_skips_existing_hero_without_force(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.recipes.recipe_gold_v3_image_pipeline.fetch_gold_v3_recipes_by_ids",
        lambda _s, ids: {
            256: _recipe(
                rid=256,
                title="Котлеты с овощами",
                hero_url="/recipe-images/256/hero.webp",
            )
        },
    )
    plan = plan_image_generation(MagicMock(), [256], images_dir=tmp_path, explicit_ids=True)
    assert plan["idempotent_full_skip"] is True
    assert plan["to_generate_count"] == 0
    assert plan["to_skip_count"] == 1


def test_plan_skips_existing_hero_file_without_force(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.recipes.recipe_gold_v3_image_pipeline.fetch_gold_v3_recipes_by_ids",
        lambda _s, ids: {256: _recipe(rid=256, title="Котлеты с овощами")},
    )
    folder = tmp_path / "256"
    folder.mkdir(parents=True)
    (folder / "hero.webp").write_bytes(b"webp")
    plan = plan_image_generation(MagicMock(), [256], images_dir=tmp_path, explicit_ids=True)
    assert plan["to_generate_count"] == 0
    assert plan["to_skip_count"] == 1


def test_plan_force_regenerates_when_hero_exists(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.recipes.recipe_gold_v3_image_pipeline.fetch_gold_v3_recipes_by_ids",
        lambda _s, ids: {
            256: _recipe(
                rid=256,
                title="Котлеты с овощами",
                hero_url="/recipe-images/256/hero.webp",
            )
        },
    )
    plan = plan_image_generation(
        MagicMock(), [256], images_dir=tmp_path, force=True, explicit_ids=True
    )
    assert plan["to_generate_count"] == 1
    assert plan["idempotent_full_skip"] is False


def test_plan_partial_batch_one_existing_one_new(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.recipes.recipe_gold_v3_image_pipeline.fetch_gold_v3_recipes_by_ids",
        lambda _s, ids: {
            256: _recipe(
                rid=256,
                title="Котлеты с овощами",
                hero_url="/recipe-images/256/hero.webp",
            ),
            257: _recipe(rid=257, title="Крупа с овощами"),
        },
    )
    plan = plan_image_generation(MagicMock(), [256, 257], images_dir=tmp_path, explicit_ids=True)
    assert plan["to_generate_count"] == 1
    assert plan["to_skip_count"] == 1
    assert plan["idempotent_full_skip"] is False


def test_plan_fails_for_non_gold_v3_recipe(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.recipes.recipe_gold_v3_image_pipeline.fetch_gold_v3_recipes_by_ids",
        lambda _s, ids: {
            99: _recipe(rid=99, title="Old manual", source_type="manual", tags=[]),
        },
    )
    plan = plan_image_generation(MagicMock(), [99], images_dir=tmp_path, explicit_ids=True)
    assert plan["ok"] is False
    assert plan["errors_by_code"].get("not_gold_v3_import") == 1


def test_plan_fails_recipe_not_found(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.recipes.recipe_gold_v3_image_pipeline.fetch_gold_v3_recipes_by_ids",
        lambda _s, ids: {},
    )
    plan = plan_image_generation(MagicMock(), [256], images_dir=tmp_path, explicit_ids=True)
    assert plan["ok"] is False
    assert plan["errors_by_code"].get("recipe_not_found") == 1


def test_check_apply_guards():
    assert check_apply_guards(apply_mode=False, max_cost_usd=None, estimated_cost_usd=1, api_configured=False)[0]
    assert not check_apply_guards(apply_mode=True, max_cost_usd=None, estimated_cost_usd=1, api_configured=True)[0]
    assert not check_apply_guards(apply_mode=True, max_cost_usd=0.5, estimated_cost_usd=0.63, api_configured=True)[0]
    assert check_apply_guards(apply_mode=True, max_cost_usd=1.0, estimated_cost_usd=0.63, api_configured=True)[0]


def test_build_public_image_urls():
    urls = build_public_image_urls(256)
    assert urls["hero_image_url"] == "/recipe-images/256/hero.webp"
    assert urls["image_url"] == "/recipe-images/256/card_800.webp"


def test_derivatives_complete(tmp_path: Path):
    folder = tmp_path / "256"
    folder.mkdir()
    for name in ("hero.webp", "card_800.webp", "thumb_400.webp"):
        (folder / name).write_bytes(b"x")
    assert derivatives_complete(256, tmp_path) is True


def test_has_existing_hero_url_or_file(tmp_path: Path):
    assert has_existing_hero(hero_image_url="/recipe-images/1/hero.webp", recipe_id=1, images_dir=tmp_path)
    folder = tmp_path / "2"
    folder.mkdir()
    (folder / "hero.webp").write_bytes(b"x")
    assert has_existing_hero(hero_image_url=None, recipe_id=2, images_dir=tmp_path)


def test_generate_script_apply_requires_max_cost(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    import sys
    from pathlib import Path

    scripts = Path(__file__).resolve().parents[3] / "backend" / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    import generate_recipe_images_v3 as gen_mod

    monkeypatch.setattr(
        sys,
        "argv",
        ["generate_recipe_images_v3.py", "--apply", "--ids", "256"],
    )
    assert gen_mod.main() == 1


def test_generate_dry_run_does_not_call_openai(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    import sys
    from pathlib import Path as P

    scripts = P(__file__).resolve().parents[3] / "backend" / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))

    import generate_recipe_images_v3 as gen_mod

    monkeypatch.setattr(gen_mod, "recipe_images_dir", lambda: tmp_path)
    monkeypatch.setattr("app.database.SessionLocal", lambda: MagicMock())
    monkeypatch.setattr(
        gen_mod,
        "plan_image_generation",
        lambda *_a, **_k: {
            "ok": True,
            "to_generate_count": 1,
            "to_skip_count": 0,
            "failed_count": 0,
            "estimated_cost_usd": 0.063,
            "idempotent_full_skip": False,
            "errors_by_code": {},
            "warnings_by_code": {},
            "targets": [{"recipe_id": 256, "status": "would_generate"}],
            "to_generate": [],
            "to_skip": [],
            "failed": [],
        },
    )
    mock_generate = MagicMock()
    monkeypatch.setattr(gen_mod, "generate_master_image", mock_generate)

    monkeypatch.setattr(sys, "argv", ["generate_recipe_images_v3.py", "--ids", "256"])
    code = gen_mod.main()
    mock_generate.assert_not_called()
    assert code == 0


def test_default_allowlist_is_256_265():
    assert list(DEFAULT_ALLOWLIST_IDS) == list(range(256, 266))


def test_plan_full_batch_cost_estimate(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.recipes.recipe_gold_v3_image_pipeline.fetch_gold_v3_recipes_by_ids",
        lambda _s, ids: {
            256: _recipe(rid=256, title="Котлеты с овощами"),
            257: _recipe(rid=257, title="Крупа с овощами"),
        },
    )
    plan = plan_image_generation(MagicMock(), [256, 257], images_dir=tmp_path, explicit_ids=True)
    assert plan["estimated_cost_usd"] == round(2 * ESTIMATED_COST_PER_IMAGE_USD, 4)
