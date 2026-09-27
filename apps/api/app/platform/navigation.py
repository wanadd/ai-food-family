from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NavigationIntent:
    kind: str
    resource_id: str | None = None
    query: str | None = None


def resolve_navigation_intent(path: str) -> NavigationIntent:
    """Resolve PLANAM meaning before a client maps it to a provider URL."""
    parts = [part for part in path.strip("/").split("/") if part]
    if not parts:
        return NavigationIntent("home")
    if parts[0] in {"recipe", "recipes"} and len(parts) == 2:
        return NavigationIntent("recipe", resource_id=parts[1])
    if parts[0] in {"plan", "plans"} and len(parts) == 2:
        return NavigationIntent("plan", resource_id=parts[1])
    if parts[0] == "shopping":
        return NavigationIntent("shopping")
    if parts[0] == "account-link" and len(parts) == 2:
        return NavigationIntent("account_link", resource_id=parts[1])
    return NavigationIntent("unknown", query=path)
