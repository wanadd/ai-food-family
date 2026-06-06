"""Tests for image-file relocation in the repair script.

Guards the 404 hotfix: files generated into the wrong folder (old batch id)
must be moved to the correct v1_import recipe folder so DB URLs resolve.
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "backend" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from repair_recipe_image_assignments import (  # noqa: E402
    REQUIRED_FILES,
    has_required_files,
    relocate_image_folder,
)


def _make_variant_folder(root: Path, recipe_id: int) -> Path:
    folder = root / str(recipe_id)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "master.png").write_bytes(b"png")
    (folder / "master.webp").write_bytes(b"webp")
    for name in REQUIRED_FILES:
        (folder / name).write_bytes(b"data")
    return folder


def test_relocate_moves_files_to_correct_id(tmp_path):
    _make_variant_folder(tmp_path, 1)  # buggy folder
    action = relocate_image_folder(1, 76, tmp_path, dry_run=False)
    assert action == "moved"
    assert has_required_files(tmp_path / "76")
    assert not (tmp_path / "1").exists()


def test_relocate_dry_run_does_not_touch_disk(tmp_path):
    _make_variant_folder(tmp_path, 8)
    action = relocate_image_folder(8, 75, tmp_path, dry_run=True)
    assert action == "would_move"
    assert (tmp_path / "8").is_dir()
    assert not (tmp_path / "75").exists()


def test_relocate_idempotent_when_dst_ready(tmp_path):
    _make_variant_folder(tmp_path, 77)  # already correct
    action = relocate_image_folder(3, 77, tmp_path, dry_run=False)
    assert action == "dst_ready"
    assert has_required_files(tmp_path / "77")


def test_relocate_missing_source(tmp_path):
    action = relocate_image_folder(99, 80, tmp_path, dry_run=False)
    assert action == "missing"
    assert not (tmp_path / "80").exists()
