#!/usr/bin/env python3
"""OpenAI image generation client for the PlanAm recipe image pipeline.

Uses a DEDICATED key (``PLANAM_IMAGE_OPENAI_API_KEY``) so image generation is
never billed against the main application key. Generates exactly ONE master
image per recipe — hero/card/thumb are produced later by cropping the master.

This module is import-safe without the ``openai`` package; the SDK is imported
lazily only when a real generation is requested.
"""

from __future__ import annotations

import base64
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-image-1"
DEFAULT_SIZE = "1536x1024"
DEFAULT_QUALITY = "medium"

# Approximate USD per image for gpt-image-1 (used when token usage is absent).
# Source: OpenAI published per-image estimates; refine after the pilot.
COST_TABLE: dict[tuple[str, str], float] = {
    ("1024x1024", "low"): 0.011,
    ("1024x1024", "medium"): 0.042,
    ("1024x1024", "high"): 0.167,
    ("1536x1024", "low"): 0.016,
    ("1536x1024", "medium"): 0.063,
    ("1536x1024", "high"): 0.25,
    ("1024x1536", "low"): 0.016,
    ("1024x1536", "medium"): 0.063,
    ("1024x1536", "high"): 0.25,
}

# Token pricing for gpt-image-1 (USD per token), used when usage is returned.
TEXT_INPUT_TOKEN_USD = 5.0 / 1_000_000
IMAGE_OUTPUT_TOKEN_USD = 40.0 / 1_000_000


class ImageGenerationError(RuntimeError):
    pass


@dataclass
class ImageGenerationResult:
    recipe_id: int | None
    title: str
    master_path: Path
    model: str
    size: str
    quality: str
    duration_s: float
    estimated_cost_usd: float
    usage: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "title": self.title,
            "master_path": str(self.master_path),
            "model": self.model,
            "size": self.size,
            "quality": self.quality,
            "duration_s": round(self.duration_s, 3),
            "estimated_cost_usd": round(self.estimated_cost_usd, 4),
            "usage": self.usage,
        }


def resolve_image_api_key() -> str | None:
    """Dedicated image key first; main app key only as fallback."""
    for var in ("PLANAM_IMAGE_OPENAI_API_KEY", "OPENAI_API_KEY"):
        value = os.environ.get(var, "").strip()
        if value:
            if var == "OPENAI_API_KEY":
                logger.warning(
                    "Using OPENAI_API_KEY fallback for image pipeline; "
                    "set PLANAM_IMAGE_OPENAI_API_KEY for isolation"
                )
            return value
    return None


def is_image_pipeline_configured() -> bool:
    return resolve_image_api_key() is not None


def estimate_cost(size: str, quality: str, usage: dict[str, Any] | None) -> float:
    if usage:
        input_tokens = int(usage.get("input_tokens") or 0)
        output_tokens = int(
            usage.get("output_tokens")
            or usage.get("image_tokens")
            or 0
        )
        if output_tokens:
            return (
                input_tokens * TEXT_INPUT_TOKEN_USD
                + output_tokens * IMAGE_OUTPUT_TOKEN_USD
            )
    return COST_TABLE.get((size, quality), COST_TABLE[(DEFAULT_SIZE, "medium")])


def _usage_to_dict(usage: Any) -> dict[str, Any]:
    if usage is None:
        return {}
    if isinstance(usage, dict):
        return usage
    for attr in ("model_dump", "to_dict", "dict"):
        method = getattr(usage, attr, None)
        if callable(method):
            try:
                result = method()
                if isinstance(result, dict):
                    return result
            except Exception:  # noqa: BLE001
                continue
    return {
        key: getattr(usage, key)
        for key in ("input_tokens", "output_tokens", "total_tokens")
        if getattr(usage, key, None) is not None
    }


def _build_client(api_key: str) -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - depends on env
        raise ImageGenerationError(
            "openai package is required. Install with: pip install openai"
        ) from exc
    return OpenAI(api_key=api_key)


def generate_master_image(
    *,
    prompt: str,
    master_path: Path,
    recipe_id: int | None = None,
    title: str = "",
    model: str = DEFAULT_MODEL,
    size: str = DEFAULT_SIZE,
    quality: str = DEFAULT_QUALITY,
    prompt_version: str = "planam_v1_home_kitchen",
    client: Any | None = None,
) -> ImageGenerationResult:
    """Generate one master image and write it to ``master_path``."""
    api_key = resolve_image_api_key()
    if client is None:
        if not api_key:
            raise ImageGenerationError(
                "No image API key. Set PLANAM_IMAGE_OPENAI_API_KEY."
            )
        client = _build_client(api_key)

    master_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    logger.info(
        "image.generate recipe_id=%s title=%r prompt_version=%s model=%s size=%s quality=%s",
        recipe_id,
        title,
        prompt_version,
        model,
        size,
        quality,
    )

    try:
        response = client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
        )
    except Exception as exc:  # noqa: BLE001
        raise ImageGenerationError(f"OpenAI image generation failed: {exc}") from exc

    duration = time.monotonic() - started
    data = getattr(response, "data", None)
    if not data:
        raise ImageGenerationError("OpenAI returned no image data")

    item = data[0]
    b64 = getattr(item, "b64_json", None)
    if not b64:
        raise ImageGenerationError(
            "OpenAI returned no base64 image (expected b64_json for gpt-image-1)"
        )
    master_path.write_bytes(base64.b64decode(b64))

    usage = _usage_to_dict(getattr(response, "usage", None))
    cost = estimate_cost(size, quality, usage)
    logger.info(
        "image.generated recipe_id=%s title=%r duration=%.2fs cost~$%.4f path=%s",
        recipe_id,
        title,
        duration,
        cost,
        master_path,
    )
    return ImageGenerationResult(
        recipe_id=recipe_id,
        title=title,
        master_path=master_path,
        model=model,
        size=size,
        quality=quality,
        duration_s=duration,
        estimated_cost_usd=cost,
        usage=usage,
    )
