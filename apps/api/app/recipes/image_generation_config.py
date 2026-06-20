"""Stage IMG: recipe image generation configuration (Gold V3 batch)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

IMAGE_PROVIDER = "openai"
IMAGE_MODEL = "gpt-image-1"
IMAGE_SIZE = "1536x1024"
IMAGE_QUALITY = "medium"
IMAGE_OUTPUT_FORMAT = "webp"
IMAGE_API_KEY_ENV_NAME = "PLANAM_IMAGE_OPENAI_API_KEY"
IMAGE_API_KEY_FALLBACK_ENV = "OPENAI_API_KEY"
IMAGE_GENERATION_ENDPOINT = "https://api.openai.com/v1/images/generations"
IMAGE_COST_SOURCE = "openai_recipe_image_client.COST_TABLE"
STYLE_VERSION = "planam_gold_v3_master"
PROMPT_VERSION = STYLE_VERSION

# Stage R Gold V3 batch — default allowlist for Stage IMG.
DEFAULT_ALLOWLIST_IDS: tuple[int, ...] = tuple(range(256, 266))

GENERATION_ENABLED_DEFAULT = False
DRY_RUN_DEFAULT = True

# USD per master image (gpt-image-1, 1536x1024, medium). See openai_recipe_image_client.
ESTIMATED_COST_PER_IMAGE_USD = 0.063

REQUIRED_DERIVATIVE_FILES = ("hero.webp", "card_800.webp", "thumb_400.webp")
MASTER_FILENAME = "master.png"


@dataclass(frozen=True)
class ImageGenerationSettings:
    provider: str = IMAGE_PROVIDER
    model: str = IMAGE_MODEL
    size: str = IMAGE_SIZE
    quality: str = IMAGE_QUALITY
    output_format: str = IMAGE_OUTPUT_FORMAT
    api_key_env_name: str = IMAGE_API_KEY_ENV_NAME
    generation_endpoint: str = IMAGE_GENERATION_ENDPOINT
    cost_per_image_usd: float = ESTIMATED_COST_PER_IMAGE_USD
    dry_run: bool = DRY_RUN_DEFAULT
    generation_enabled: bool = GENERATION_ENABLED_DEFAULT

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "size": self.size,
            "quality": self.quality,
            "output_format": self.output_format,
            "api_key_env_name": self.api_key_env_name,
            "generation_endpoint": self.generation_endpoint,
            "cost_per_image_usd": self.cost_per_image_usd,
            "dry_run": self.dry_run,
            "generation_enabled": self.generation_enabled,
            "style_version": STYLE_VERSION,
            "cost_source": IMAGE_COST_SOURCE,
        }


def get_settings(*, dry_run: bool = True, generation_enabled: bool = False) -> ImageGenerationSettings:
    return ImageGenerationSettings(
        dry_run=dry_run,
        generation_enabled=generation_enabled and not dry_run,
    )


def api_key_status() -> dict[str, Any]:
    """Report key presence only — never return or log the secret value."""
    primary = os.environ.get(IMAGE_API_KEY_ENV_NAME, "").strip()
    if primary:
        return {
            "configured": True,
            "env_name": IMAGE_API_KEY_ENV_NAME,
            "uses_fallback": False,
        }
    fallback = os.environ.get(IMAGE_API_KEY_FALLBACK_ENV, "").strip()
    if fallback:
        return {
            "configured": True,
            "env_name": IMAGE_API_KEY_FALLBACK_ENV,
            "uses_fallback": True,
            "warning": (
                f"Using {IMAGE_API_KEY_FALLBACK_ENV} fallback; "
                f"set {IMAGE_API_KEY_ENV_NAME} for billing isolation"
            ),
        }
    return {
        "configured": False,
        "env_name": IMAGE_API_KEY_ENV_NAME,
        "uses_fallback": False,
    }


def estimate_batch_cost_usd(count: int, *, cost_per_image: float = ESTIMATED_COST_PER_IMAGE_USD) -> float:
    return round(max(0, count) * cost_per_image, 4)


def validate_max_cost_usd(estimated_total: float, max_cost_usd: float | None) -> tuple[bool, str | None]:
    if max_cost_usd is None:
        return False, "max_cost_usd_required"
    if estimated_total > max_cost_usd + 1e-9:
        return False, "estimated_cost_exceeds_max"
    return True, None
