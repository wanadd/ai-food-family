"""Immutable build provenance contracts for cutover artifacts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping


REVISION_LABEL = "org.opencontainers.image.revision"
CREATED_LABEL = "org.opencontainers.image.created"
SOURCE_LABEL = "org.opencontainers.image.source"
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class ProvenanceError(ValueError):
    """Raised when an artifact cannot be tied to an immutable source revision."""


@dataclass(frozen=True)
class BuildProvenance:
    source_revision: str
    image_id: str
    image_digest: str
    dockerfile: str
    build_context: str
    production_command: str
    built_at: str

    def __post_init__(self) -> None:
        if not _SHA_RE.fullmatch(self.source_revision):
            raise ProvenanceError("source_revision must be a full 40-character git SHA")
        for name in ("image_id", "image_digest", "dockerfile", "build_context", "production_command", "built_at"):
            if not getattr(self, name).strip():
                raise ProvenanceError(f"{name} is required")


def build_labels(source_revision: str, *, built_at: str | None = None) -> dict[str, str]:
    if not _SHA_RE.fullmatch(source_revision):
        raise ProvenanceError("source_revision must be a full 40-character git SHA")
    return {
        REVISION_LABEL: source_revision,
        CREATED_LABEL: built_at or datetime.now(timezone.utc).isoformat(),
        SOURCE_LABEL: "planam/ai-food-family",
    }


def verify_image_provenance(labels: Mapping[str, str], expected_revision: str) -> None:
    if not _SHA_RE.fullmatch(expected_revision):
        raise ProvenanceError("expected_revision must be a full 40-character git SHA")
    actual = labels.get(REVISION_LABEL)
    if actual != expected_revision:
        raise ProvenanceError(f"artifact revision mismatch: expected {expected_revision}, got {actual!r}")
    if not labels.get(CREATED_LABEL):
        raise ProvenanceError("artifact build timestamp is missing")


def verify_build_pair(api: Mapping[str, str], web: Mapping[str, str], expected_revision: str) -> None:
    verify_image_provenance(api, expected_revision)
    verify_image_provenance(web, expected_revision)
    if api.get(REVISION_LABEL) != web.get(REVISION_LABEL):
        raise ProvenanceError("API and web artifacts have different source revisions")
