from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class V2Error(Exception):
    code: str
    message: str
    status_code: int
    details: dict[str, Any] | None = None


ERROR_MESSAGES = {
    "authentication_required": "Authentication is required.",
    "invalid_session": "The session is invalid or expired.",
    "forbidden": "The requested operation is not allowed.",
    "identity_conflict": "The external identity is already bound elsewhere.",
    "link_expired": "The identity link intent has expired.",
    "link_replayed": "The identity link intent has already been consumed.",
    "validation_error": "The request is invalid.",
    "not_found": "The requested resource was not found.",
    "conflict": "The request conflicts with current state.",
    "entitlement_required": "The requested capability is not available.",
    "permission_required": "The required permission is not available.",
    "last_identity": "At least one usable authentication method must remain.",
}


def error(code: str, status_code: int, *, details: dict[str, Any] | None = None) -> V2Error:
    return V2Error(code, ERROR_MESSAGES.get(code, "The request could not be completed."), status_code, details)
