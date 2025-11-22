from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

from PIL import Image


MAX_SIZE = (700, 700)
QUALITY = 70
VALID_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff")


def to_rgb(image: Image.Image) -> Image.Image:
    if image.mode in ("RGB", "L"):
        return image.convert("RGB")

    if image.mode == "P":
        image = image.convert("RGBA")

    if image.mode in ("RGBA", "LA"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        mask = image.getchannel("A") if "A" in image.getbands() else None
        background.paste(image.convert("RGB"), mask=mask)
        return background

    return image.convert("RGB")


def create_preview(image_path: Path, preview_dir: Path) -> Path:
    with Image.open(image_path) as img:
        img = to_rgb(img)
        img.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)

        preview_dir.mkdir(parents=True, exist_ok=True)
        original_name = image_path.name
        name_parts = original_name.rsplit(".", 1)
        preview_name = f"{name_parts[0]}_preview.jpg"
        preview_path = preview_dir / preview_name
        img.save(preview_path, format="JPEG", quality=QUALITY, optimize=True)
        return preview_path


def iter_source_images(images_dir: Path) -> Iterable[Path]:
    for entry in images_dir.iterdir():
        if entry.is_dir() or entry.suffix.lower() not in VALID_EXTENSIONS:
            continue
        yield entry


def main() -> int:
    root_dir = Path(__file__).resolve().parent.parent
    images_dir = root_dir / "media" / "images"
    preview_dir = images_dir / "preview"

    if not images_dir.exists():
        print(f"[!] Images directory not found: {images_dir}")
        return 1

    generated = 0
    errors: list[tuple[Path, Exception]] = []

    for image_path in iter_source_images(images_dir):
        try:
            create_preview(image_path, preview_dir)
            generated += 1
            print(f"[+] Preview saved for {image_path.name}")
        except Exception as exc:
            errors.append((image_path, exc))
            print(f"[x] Failed for {image_path.name}: {exc}")

    print(f"\nDone. Generated {generated} previews into {preview_dir}.")
    if errors:
        print("The following images failed:")
        for path, exc in errors:
            print(f" - {path.name}: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

