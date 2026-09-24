"""v2 baseline revision

Revision ID: 20260922_0001
Revises:
Create Date: 2026-09-22
"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "20260922_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = ("v2_foundation",)
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Baseline marker only; Wave 01 creates no V2 application tables."""


def downgrade() -> None:
    """Baseline marker only; no application objects are removed."""
