"""Shared path resolution for recipe-image scripts.

Works in two layouts:
  * Local repo:   <repo>/apps/api/app/...        scripts run from <repo>/backend/scripts
  * API container: /app/app/...                  scripts mounted at /app/backend/scripts

Image storage path is driven by ``RECIPE_IMAGES_DIR`` (physical dir inside the
container) with a safe local fallback, and ``RECIPE_IMAGES_PUBLIC_URL`` for the
public URL prefix.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

DEFAULT_PUBLIC_URL = "/recipe-images"


def find_app_root() -> Path | None:
    """Locate the directory that contains the ``app`` package (app/database.py)."""
    start = SCRIPTS_DIR
    for parent in [start, *start.parents]:
        for candidate in (parent, parent / "apps" / "api"):
            if (candidate / "app" / "database.py").is_file():
                return candidate
    return None


def ensure_app_on_path() -> Path:
    """Put the API root and scripts dir on sys.path; return the API root."""
    api_root = find_app_root()
    if api_root is None:
        raise SystemExit(
            "Could not locate the 'app' package. Run inside the repo or the api container."
        )
    for path in (str(SCRIPTS_DIR), str(api_root)):
        if path not in sys.path:
            sys.path.insert(0, path)
    return api_root


def recipe_images_dir() -> Path:
    """Physical directory holding recipe image folders.

    Priority: RECIPE_IMAGES_DIR env, then local <repo>/apps/web/public/recipe-images,
    then <api_root>/public/recipe-images.
    """
    env = os.environ.get("RECIPE_IMAGES_DIR", "").strip()
    if env:
        return Path(env)
    api_root = find_app_root()
    if api_root is not None:
        web_public = api_root.parent / "web" / "public" / "recipe-images"
        if (api_root.parent / "web").is_dir():
            return web_public
        return api_root / "public" / "recipe-images"
    return SCRIPTS_DIR.parents[1] / "apps" / "web" / "public" / "recipe-images"


def recipe_images_public_url() -> str:
    """Public URL prefix for serving recipe images (no trailing slash)."""
    return os.environ.get("RECIPE_IMAGES_PUBLIC_URL", DEFAULT_PUBLIC_URL).rstrip("/")


def find_repo_file(*relative_parts: str) -> Path:
    """Resolve a repo-relative file across local and container layouts.

    Supports:
    - API container: /app
    - local repo root: <repo>
    - local API root: <repo>/apps/api

    The function must never crash on shallow paths such as /app.
    It returns the first existing candidate, otherwise the first safe candidate.
    """
    candidates: list[Path] = []

    def add_candidate(candidate: Path) -> None:
        candidate = candidate.resolve()
        if candidate not in candidates:
            candidates.append(candidate)

    api_root = find_app_root()
    if api_root is not None:
        add_candidate(api_root.joinpath(*relative_parts))

        # API container layout: /app/app/database.py, reports live in /app/reports.
        add_candidate(api_root.parent.joinpath(*relative_parts))

        # Local layout: <repo>/apps/api/app/database.py, reports live in <repo>/reports.
        if len(api_root.parents) >= 2:
            add_candidate(api_root.parents[1].joinpath(*relative_parts))

    # Script layout fallback: /app/backend/scripts -> /app/reports.
    if len(SCRIPTS_DIR.parents) >= 2:
        add_candidate(SCRIPTS_DIR.parents[1].joinpath(*relative_parts))

    if not candidates:
        return Path(*relative_parts)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]
