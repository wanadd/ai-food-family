"""Shared helpers for Recipe Engine HTTP routes."""

from fastapi import HTTPException, status


def require_feature(enabled: bool, env_name: str) -> None:
    if not enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Recipe Engine feature is disabled ({env_name}=false)",
        )
