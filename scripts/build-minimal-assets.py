"""Typeset and slice the profile's text-free Google Flow artwork.

Usage: uv run --with pillow python scripts/build-minimal-assets.py <art.jpg> <out-dir>

Rebuilding requires macOS's installed SF Rounded font. The font itself is not
copied or distributed; GitHub only displays the resulting raster images.
"""

import sys
from pathlib import Path
from shutil import copyfile

from PIL import Image, ImageDraw, ImageFont


BACKGROUND = (250, 250, 252)
INK = (29, 29, 31)
SECONDARY = (103, 103, 111)
LINK = (70, 70, 77)
FONT_PATH = "/System/Library/Fonts/SFNSRounded.ttf"

# The link crops partition the entire row, including its blank background.
# README widths match these proportions separately for desktop and mobile.
SLICES = {
    "desktop": {
        "header": (0, 0, 1760, 704),
        "project": (0, 704, 1760, 890),
        "website": (0, 890, 304, 974),
        "source": (304, 890, 1760, 974),
        "stack": (0, 974, 1760, 1104),
    },
    "mobile": {
        "header": (0, 0, 720, 548),
        "project": (0, 548, 720, 697),
        "website": (0, 697, 248, 781),
        "source": (248, 697, 720, 781),
        "stack": (0, 781, 720, 956),
    },
}


def font(size, weight="Regular"):
    face = ImageFont.truetype(FONT_PATH, size)
    face.set_variation_by_name(weight)
    return face


def text(canvas, position, value, size, weight="Regular", color=INK, anchor="lt"):
    draw = ImageDraw.Draw(canvas)
    face = font(size, weight)
    bounds = draw.textbbox(position, value, font=face, anchor=anchor)
    if not (0 <= bounds[0] <= bounds[2] <= canvas.width
            and 0 <= bounds[1] <= bounds[3] <= canvas.height):
        raise ValueError(f"Text outside canvas: {value!r}, {bounds}")
    draw.text(position, value, font=face, fill=color, anchor=anchor)
    return bounds


def link(canvas, position, value, size):
    baseline = (position[0], position[1] + size)
    bounds = text(canvas, baseline, value, size, color=LINK, anchor="ls")
    ImageDraw.Draw(canvas).line(
        (bounds[0], baseline[1] + 9, bounds[2], baseline[1] + 9),
        fill=(175, 175, 183), width=1,
    )


def atmosphere(source, size, fade):
    artwork = source.resize(size, Image.Resampling.LANCZOS)
    mask = Image.new("L", size)
    draw = ImageDraw.Draw(mask)
    for y in range(size[1]):
        opacity = round(215 * min(1, y / fade, (size[1] - 1 - y) / fade))
        draw.line((0, y, size[0] - 1, y), fill=opacity)
    return Image.composite(artwork, Image.new("RGB", size, BACKGROUND), mask)


def desktop(source):
    canvas = Image.new("RGB", (1760, 1104), BACKGROUND)
    artwork = source.crop((0, 80, source.width, 630))
    canvas.paste(atmosphere(artwork, (1760, 704), 50), (0, 0))
    text(canvas, (104, 150), "Natan Viana", 96, "Semibold")
    text(canvas, (104, 280), "Web & mobile developer", 40, color=SECONDARY)
    link(canvas, (104, 365), "Check my portfolio", 28)

    text(canvas, (104, 778), "Uncached", 40, "Medium")
    text(canvas, (104, 841), "Disk cleanup for developers.", 32,
         color=SECONDARY)
    link(canvas, (104, 903), "uncached.app", 28)
    link(canvas, (326, 903), "source", 28)

    text(canvas, (104, 1008),
         "Rust · TypeScript · JavaScript · Python · React · Node.js", 24,
         color=SECONDARY)
    text(canvas, (104, 1048),
         "Tauri · Astro · Cloudflare · Godot · and more", 24, color=SECONDARY)
    return canvas


def mobile(source):
    canvas = Image.new("RGB", (720, 956), BACKGROUND)
    artwork = source.crop((0, 180, source.width, 740))
    canvas.paste(atmosphere(artwork, (720, 293), 45), (0, 230))
    text(canvas, (48, 64), "Natan Viana", 68, "Semibold")
    text(canvas, (48, 162), "Web & mobile developer", 32, color=SECONDARY)
    link(canvas, (48, 270), "Check my portfolio", 28)

    text(canvas, (48, 586), "Uncached", 40, "Medium")
    text(canvas, (48, 649), "Disk cleanup for developers.", 30, color=SECONDARY)
    link(canvas, (48, 711), "uncached.app", 28)
    link(canvas, (270, 711), "source", 28)

    for y, line in zip((817, 857, 897), (
        "Rust · TypeScript · JavaScript · Python",
        "React · Node.js · Tauri · Astro",
        "Cloudflare · Godot · and more",
    )):
        text(canvas, (48, y), line, 24, color=SECONDARY)
    return canvas


def save_png(image, path):
    image.save(path, optimize=True)
    print(f"{path}: {image.size}, {path.stat().st_size:,} bytes")


def main():
    source_path = Path(sys.argv[1])
    source = Image.open(source_path).convert("RGB")
    if source.size != (1376, 768):
        raise ValueError(f"Unexpected source dimensions: {source.size}")
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    if source_path.resolve() != (out / "artwork.jpg").resolve():
        copyfile(source_path, out / "artwork.jpg")
    for variant, image in (("desktop", desktop(source)), ("mobile", mobile(source))):
        save_png(image, out / f"composition-{variant}.png")
        for name, box in SLICES[variant].items():
            save_png(image.crop(box), out / f"{name}-{variant}.png")


if __name__ == "__main__":
    main()
