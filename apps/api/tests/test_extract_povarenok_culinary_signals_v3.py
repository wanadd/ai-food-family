"""Tests for Povarenok culinary signals extractor (Stage D)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "backend" / "scripts" / "extract_povarenok_culinary_signals_v3.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "extract_povarenok_culinary_signals_v3", SCRIPT
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["extract_povarenok_culinary_signals_v3"] = mod
    spec.loader.exec_module(mod)
    return mod


mod = _load_module()


def _record(
    *,
    title: str,
    ingredients: list[str],
    source_url: str = "https://www.povarenok.ru/recipes/show/99999/",
) -> dict:
    return {
        "source": "povarenok",
        "source_url": source_url,
        "title": title,
        "ingredients": [{"name": name} for name in ingredients],
        "steps": [],
    }


def test_signal_has_no_original_title_field():
    signal, skip = mod.extract_signal_from_record(
        _record(title="Салат овощной", ingredients=["огурец", "помидор", "лук"]),
        index=1,
    )
    assert skip is None
    assert signal is not None
    assert "title" not in signal
    assert "original_title" not in signal


def test_signal_has_no_steps_field():
    signal, _ = mod.extract_signal_from_record(
        _record(title="Куриный суп", ingredients=["курица", "морковь", "лук"]),
        index=2,
    )
    assert signal is not None
    assert "steps" not in signal
    assert "original_steps" not in signal


def test_alcohol_record_marked_avoid():
    signal, _ = mod.extract_signal_from_record(
        _record(
            title="Наливка из вишни на водке",
            ingredients=["вишня", "водка", "сахар"],
        ),
        index=3,
    )
    assert signal is not None
    assert signal["avoid_for_planam"] is True
    assert "has_alcohol" in signal["quality_flags"]


def test_pork_produces_restriction_and_quality_hints():
    signal, _ = mod.extract_signal_from_record(
        _record(
            title="Свиные ребрышки с картофелем",
            ingredients=["ребра свиные", "картофель", "лук", "морковь"],
        ),
        index=4,
    )
    assert signal is not None
    assert "no_pork" in signal["restriction_hints"]
    assert "has_pork" in signal["quality_flags"]


def test_eggs_milk_allergen_hints():
    signal, _ = mod.extract_signal_from_record(
        _record(
            title="Запеканка творожная",
            ingredients=["творог", "яйцо куриное", "молоко", "сахар"],
        ),
        index=5,
    )
    assert signal is not None
    assert "eggs" in signal["allergen_hints"]
    assert "milk" in signal["allergen_hints"]


def test_dessert_marked_avoid_or_flag():
    signal, _ = mod.extract_signal_from_record(
        _record(
            title="Торт шоколадный домашний",
            ingredients=["мука", "яйца", "сахар", "какао", "сливки"],
        ),
        index=6,
    )
    assert signal is not None
    assert signal["avoid_for_planam"] or "likely_dessert" in signal["quality_flags"]


def test_ingredient_groups_detected():
    signal, _ = mod.extract_signal_from_record(
        _record(
            title="Курица с рисом",
            ingredients=["грудка куриная", "рис", "морковь", "лук"],
        ),
        index=7,
    )
    assert signal is not None
    assert "мясо_птица" in signal["main_product_groups"]
    assert "крупы" in signal["main_product_groups"] or "крупы" in signal.get(
        "secondary_product_groups", []
    )


def test_originality_safety_rejects_original_title_key():
    bad = {
        "signal_id": "pov_sig_test",
        "original_title": "Секретный рецепт",
        "generation_prompt_hints": ["ok"],
    }
    assert mod.validate_output_signal(bad, source_title="Секретный рецепт") is not None


def test_source_url_not_exposed_only_hash():
    record = _record(
        title="Гречка с грибами",
        ingredients=["гречка", "шампиньоны", "лук", "масло"],
    )
    signal, _ = mod.extract_signal_from_record(record, index=8)
    assert signal is not None
    assert "source_url" not in signal
    assert signal["source_record_hash"]
    assert "povarenok.ru" not in json.dumps(signal, ensure_ascii=False)


def test_dry_run_does_not_write_output(tmp_path):
    input_path = tmp_path / "in.jsonl"
    output_path = tmp_path / "out.jsonl"
    input_path.write_text(
        json.dumps(
            _record(title="Овощной суп", ingredients=["картофель", "морковь", "лук"]),
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    result = mod.run_extraction(
        input_path=input_path,
        output_path=output_path,
        report_path=tmp_path / "report.md",
        limit=10,
        sample_size=1,
        dry_run=True,
    )
    assert result["signals_written"] == 1
    assert not output_path.exists()
