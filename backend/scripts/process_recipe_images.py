#!/usr/bin/env python3
"""Derive hero, card, and thumbnail WebP images from one master image.

One master per recipe — no separate AI generations for variants.

Run from the repository root:
    python backend/scripts/process_recipe_images.py --master path/to/master.png --recipe-id 42
    python backend/scripts/process_recipe_images.py --master master.webp --output-dir public/recipe-images/42

Requires: pip install Pillow
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from _image_paths import recipe_images_dir  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

# master 3:2 landscape; crops preserve focus on dish center
VARIANTS: dict[str, tuple[int, int]] = {
    "hero": (1200, 675),
    "card_800": (800, 800),
    "thumb_400": (400, 400),
}


def load_pillow():
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit(
            "Pillow is required. Install with: pip install Pillow"
        ) from exc
    return Image


def center_crop_cover(image, target_w: int, target_h: int):
    """Scale to cover target box, then center-crop."""
    src_w, src_h = image.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w = int(round(src_w * scale))
    new_h = int(round(src_h * scale))
    resized = image.resize((new_w, new_h), resample=3)  # BICUBIC
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def save_webp(image, path: Path, *, quality: int = 82) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")
    image.save(path, format="WEBP", quality=quality, method=6)


def process_master(
    master_path: Path,
    output_dir: Path,
    *,
    quality: int = 82,
    save_master_copy: bool = True,
) -> dict[str, Path]:
    Image = load_pillow()
    if not master_path.exists():
        raise SystemExit(f"Master image not found: {master_path}")

    with Image.open(master_path) as img:
        rgb = img.convert("RGB")
        outputs: dict[str, Path] = {}
        output_dir.mkdir(parents=True, exist_ok=True)

        if save_master_copy:
            master_out = output_dir / "master.webp"
            save_webp(rgb, master_out, quality=quality)
            outputs["master"] = master_out

        for name, size in VARIANTS.items():
            cropped = center_crop_cover(rgb, size[0], size[1])
            out_path = output_dir / f"{name}.webp"
            save_webp(cropped, out_path, quality=quality)
            outputs[name] = out_path

        hero_path = output_dir / "hero.webp"
        outputs["hero"] = hero_path

    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create hero/card/thumb WebP crops from one master image"
    )
    parser.add_argument("--master", required=True, help="Path to master image file")
    parser.add_argument(
        "--recipe-id",
        type=int,
        help="Recipe ID (used for default output dir)",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory (default: public/recipe-images/{recipe_id})",
    )
    parser.add_argument("--quality", type=int, default=82, help="WebP quality 1-100")
    parser.add_argument(
        "--no-master-copy",
        action="store_true",
        help="Skip writing master.webp copy",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    master_path = Path(args.master).expanduser().resolve()

    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser().resolve()
    elif args.recipe_id is not None:
        output_dir = recipe_images_dir() / str(args.recipe_id)
    else:
        raise SystemExit("Provide --output-dir or --recipe-id")

    outputs = process_master(
        master_path,
        output_dir,
        quality=args.quality,
        save_master_copy=not args.no_master_copy,
    )
    for key, path in outputs.items():
        print(f"{key}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
