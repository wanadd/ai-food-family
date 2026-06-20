"""Tests for Recipe Rebuild V2 safe reset classification."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "backend" / "scripts" / "recipe_rebuild_v2_safe_reset.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("recipe_rebuild_v2_safe_reset", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["recipe_rebuild_v2_safe_reset"] = mod
    spec.loader.exec_module(mod)
    return mod


mod = _load_module()


@pytest.mark.parametrize(
    "tags",
    [
        ["gold_v2"],
        ["recipe_schema_v2"],
        ["status:gold"],
        ["gold_v2", "breakfast_omelet", "recipe_schema_v2", "status:gold"],
    ],
)
def test_gold_tags_never_deletable(tags: list[str]):
    kind, info = mod.classify_reset_candidate(
        recipe_id=2,
        title="Омлет с овощами",
        source_type="seed",
        tags=tags,
        protected_ids=set(),
    )
    assert kind == "blocked"
    assert info["reason"] == "gold_recipe_v2"


@pytest.mark.parametrize(
    ("source_type", "tags"),
    [
        ("import", []),
        ("v1_import", ["legacy"]),
        ("seed", ["breakfast"]),
    ],
)
def test_legacy_import_without_protection_remains_deletable(source_type: str, tags: list[str]):
    kind, info = mod.classify_reset_candidate(
        recipe_id=99,
        title="Legacy soup",
        source_type=source_type,
        tags=tags,
        protected_ids=set(),
    )
    assert kind == "deletable"
    assert info["source_type"] == source_type


def test_favorites_protection_still_blocks_non_gold():
    kind, info = mod.classify_reset_candidate(
        recipe_id=10,
        title="Old seed",
        source_type="seed",
        tags=[],
        protected_ids={10},
    )
    assert kind == "blocked"
    assert info["reason"] == "has_favorites_history_or_checkins"


def test_analyze_candidates_counts_gold_protected():
    candidates = [
        (1, "Legacy", "import", []),
        (2, "Омлет с овощами", "seed", ["gold_v2", "recipe_schema_v2", "status:gold"]),
        (3, "Another legacy", "v1_import", None),
    ]
    result = mod.analyze_candidates(candidates, protected_ids=set())
    assert result["candidate_count"] == 3
    assert result["deletable_count"] == 2
    assert result["blocked_count"] == 1
    assert result["protected_gold_status"] == 1
    assert 2 not in result["deletable_ids"]
