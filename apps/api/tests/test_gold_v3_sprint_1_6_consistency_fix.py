from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _load_script(name: str):
    path = ROOT / "backend" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _ingredients(*names: str):
    return [{"name": name} for name in names]


def _steps(*texts: str):
    return [{"text": text} for text in texts]


def test_generic_fish_step_is_flagged_before_cleanup():
    from app.services.recipes.step_display import step_has_absent_fish_reference

    step = "Подготовьте филе индейки, гречка, морковь: мясо, рыбу или овощи нарежьте порционными кусками."
    assert step_has_absent_fish_reference(step, _ingredients("филе индейки", "гречка", "морковь"))


def test_user_facing_cleanup_removes_absent_fish_reference():
    from app.services.recipes.step_display import public_recipe_steps

    steps = [
        "Подготовьте филе индейки, гречка, морковь: мясо, рыбу или овощи нарежьте порционными кусками.",
        "Выложите ингредиенты в форму.",
    ]
    cleaned = public_recipe_steps(235, steps, _ingredients("филе индейки", "гречка", "морковь"))
    assert "рыб" not in cleaned[0].lower()
    assert "индейк" in cleaned[0].lower()
    assert "греч" in cleaned[0].lower()


def test_fish_recipe_can_still_mention_fish():
    from app.services.recipes.step_display import public_recipe_steps

    steps = ["Рыбу нарежьте порционными кусками и сбрызните лимоном."]
    cleaned = public_recipe_steps(233, steps, _ingredients("треска", "лимон", "масло"))
    assert "рыб" in cleaned[0].lower()


def test_affected_cleanup_ids_are_exact():
    from app.services.recipes.step_display import GENERIC_FISH_STEP_FIX_IDS

    assert GENERIC_FISH_STEP_FIX_IDS == {235, 239, 242, 245, 246}


def test_clean_title_helper_removes_known_problem_terms():
    from app.services.recipes.title_display import public_recipe_title

    assert public_recipe_title("Халяль-курица с булгуром") == "Курица с булгуром"
    assert public_recipe_title("Постный гороховый суп") == "Гороховый суп с овощами"
    assert public_recipe_title("Быстрый стир-фрай с курицей") == "Курица с овощами на сковороде"
    assert public_recipe_title("Лёгкий ужин: салат с тунцом") == "Салат с тунцом и овощами"


def test_consistency_audit_returns_no_hard_fail_on_fixed_sample():
    audit = _load_script("audit_gold_v3_recipe_consistency")
    row = {
        "id": 235,
        "title": "Гречка с индейкой",
        "display_title": "Гречка с индейкой",
        "description": "Гречка с индейкой и морковью.",
        "tags": [],
    }
    item = audit.evaluate_recipe_consistency(
        row,
        _ingredients("филе индейки", "гречка", "морковь"),
        _steps(
            "Подготовьте филе индейки, гречка, морковь: мясо, рыбу или овощи нарежьте порционными кусками.",
            "Выложите ингредиенты в форму или на сковороду, добавьте специи и немного масла.",
            "Готовьте до полной готовности, затем дайте блюду постоять 3-5 минут перед подачей.",
        ),
    )
    assert item["hard_fail"] == []
    assert item["raw_steps_changed"] is True


def test_no_raw_json_or_source_leakage_introduced():
    from app.services.recipes.step_display import public_recipe_steps

    cleaned = public_recipe_steps(
        246,
        ["Подготовьте куриное филе, перец, морковь: мясо, рыбу или овощи нарежьте порционными кусками."],
        _ingredients("куриное филе", "перец", "морковь"),
    )
    text = " ".join(cleaned).lower()
    assert "source_url" not in text
    assert "povarenok" not in text
    assert "{" not in text
    assert "}" not in text
