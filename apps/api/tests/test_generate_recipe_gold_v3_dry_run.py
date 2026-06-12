"""Tests for Gold V3 dry-run generator script."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
SCRIPT = ROOT / "backend" / "scripts" / "generate_recipe_gold_v3_dry_run.py"
SIGNALS = ROOT / "exports" / "povarenok_culinary_signals_v3_100.jsonl"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


def _load_mod():
    spec = importlib.util.spec_from_file_location("generate_recipe_gold_v3_dry_run", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["generate_recipe_gold_v3_dry_run"] = mod
    spec.loader.exec_module(mod)
    return mod


mod = _load_mod()


def test_reads_signals():
    signals = mod.load_jsonl(SIGNALS)
    assert len(signals) >= 10


def test_skips_avoid_when_enough_signals():
    signals = mod.load_jsonl(SIGNALS)
    selected = mod.select_diverse_signals(signals, 10, prefer_non_avoid=True)
    assert len(selected) == 10
    assert all(not s.get("avoid_for_planam") for s in selected)


def test_selects_diverse_signals():
    signals = mod.load_jsonl(SIGNALS)
    selected = mod.select_diverse_signals(signals, 5)
    families = {s.get("dish_family") for s in selected}
    assert len(families) >= 2


def test_no_api_recipe_passes_validator():
    signals = mod.load_jsonl(SIGNALS)
    good = [s for s in signals if not s.get("avoid_for_planam")][:1]
    recipe = mod.build_no_api_recipe(good[0], 1)
    recipe = mod.enrich_recipe_metadata(recipe, good[0])
    from app.recipes.recipe_gold_v3_validation import validate_recipe_gold_v3

    assert not mod.originality_post_check(recipe)
    result = validate_recipe_gold_v3(recipe)
    assert result.ok, [e.code for e in result.errors]


def test_originality_post_check_rejects_forbidden_fields():
    recipe = mod.build_no_api_recipe({"signal_id": "x", "dish_family": "суп"}, 1)
    recipe["source_url"] = "https://example.com"
    assert mod.originality_post_check(recipe)


def test_cost_guard_blocks_low_budget():
    ok, est = mod.check_cost_guard(limit=10, retry_invalid=1, max_cost_usd=0.01)
    assert not ok
    assert est > 0.01


def test_dry_run_no_api_cli(tmp_path):
    out = tmp_path / "out.jsonl"
    report = tmp_path / "report.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--signals",
            str(SIGNALS),
            "--output",
            str(out),
            "--report",
            str(report),
            "--limit",
            "3",
            "--dry-run",
            "--no-api",
            "--max-cost-usd",
            "0.01",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert out.exists()
    lines = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 3
    assert report.exists()
    assert "source_url" not in out.read_text(encoding="utf-8")
