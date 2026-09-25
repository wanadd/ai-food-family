"""Read-only artifact delivery verification.

Fetching and deployment are owned by the deployment runner. This module only
verifies an advertised immutable target and its image provenance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from app.cutover.provenance import verify_build_pair


class ArtifactDeliveryError(ValueError):
    pass


@dataclass(frozen=True)
class ArtifactDeliveryContract:
    target_revision: str
    authoritative_source: str
    accepted_ref: str = "refs/heads/main"

    def verify_target(self, *, advertised_refs: Mapping[str, str], reachable_revisions: Iterable[str], api_labels: Mapping[str, str], web_labels: Mapping[str, str]) -> None:
        if advertised_refs.get(self.accepted_ref) != self.target_revision:
            raise ArtifactDeliveryError("authoritative ref does not advertise the requested target")
        if self.target_revision not in set(reachable_revisions):
            raise ArtifactDeliveryError("requested target is not reachable from the authoritative source")
        try:
            verify_build_pair(api_labels, web_labels, self.target_revision)
        except ValueError as exc:
            raise ArtifactDeliveryError(str(exc)) from exc
