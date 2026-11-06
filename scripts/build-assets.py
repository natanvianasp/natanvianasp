"""Builds the profile assets from a Google Flow pixel-art sheet.

Usage: python build-assets.py <sheet.jpg> <out-dir>

The sheet is resampled onto its native pixel grid (STEP source pixels per art
pixel, phase OFFSET_X/OFFSET_Y), reduced to PALETTE_SIZE colours, cut into its
items, labelled with a 5x7 bitmap font at TEXT_DENSITY pixels per art pixel,
and written at SCALE device pixels per art pixel. README widths are art width
* SCALE / 2 so retina screens get exact integer scaling.
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

STEP, OFFSET_X, OFFSET_Y = 5.74, 0.0, 2.8
PALETTE_SIZE = 64
SCALE = 8
TEXT_DENSITY = 2
WHITE_THRESHOLD = 235

BANNER_BOX = (13, 10, 227, 59)
TASKBAR_BOX = (10, 111, 230, 125)
ICON_ROW = (73, 99)
ICON_COLUMNS = ((15, 36), (51, 76), (89, 113), (128, 149), (164, 189))
ICON_NAMES = ("uncached", "core", "desktop", "website", "portfolio")
ICON_LABELS = ("UNCACHED", "CORE", "DESKTOP", "WEBSITE", "PORTFOLIO")
ICON_TILE = (40, 36)

INK = (20, 20, 15)
WHITE = (255, 255, 255)

GLYPH_WIDTH, GLYPH_HEIGHT = 5, 7
GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    " ": ("00000",) * 7,
}


def resample(sheet: np.ndarray) -> np.ndarray:
    columns = int((sheet.shape[1] - OFFSET_X) // STEP)
    rows = int((sheet.shape[0] - OFFSET_Y) // STEP)
    inset = int(STEP) - 1
    art = np.zeros((rows, columns, 3), dtype=np.uint8)
    for row in range(rows):
        for column in range(columns):
            y0, x0 = int(OFFSET_Y + row * STEP), int(OFFSET_X + column * STEP)
            block = sheet[y0 + 1:y0 + inset, x0 + 1:x0 + inset].reshape(-1, 3)
            art[row, column] = np.median(block, axis=0)
    quantized = Image.fromarray(art).quantize(PALETTE_SIZE, method=Image.Quantize.MAXCOVERAGE)
    return np.asarray(quantized.convert("RGB")).copy()


def text_width(text: str) -> int:
    return len(text) * (GLYPH_WIDTH + 1) - 1


def draw_text(canvas: np.ndarray, text: str, x: int, y: int, color) -> None:
    for index, char in enumerate(text):
        for row, bits in enumerate(GLYPHS[char]):
            for column, bit in enumerate(bits):
                if bit == "1":
                    canvas[y + row, x + index * (GLYPH_WIDTH + 1) + column] = (*color, 255)


def draw_label(tile: np.ndarray, label: str) -> None:
    """Ink-bordered white tag on the bottom rows, readable on light and dark themes."""
    width = text_width(label) + 6
    left = (tile.shape[1] - width) // 2
    top = tile.shape[0] - GLYPH_HEIGHT - 5
    tile[top:top + GLYPH_HEIGHT + 4, left:left + width] = (*INK, 255)
    tile[top + 1:top + GLYPH_HEIGHT + 3, left + 1:left + width - 1] = (*WHITE, 255)
    draw_text(tile, label, left + 3, top + 2, INK)


def refine(rgba: np.ndarray) -> np.ndarray:
    """Splits every art pixel into TEXT_DENSITY^2 so text can use half-size pixels."""
    return rgba.repeat(TEXT_DENSITY, axis=0).repeat(TEXT_DENSITY, axis=1)


def to_rgba(art: np.ndarray) -> np.ndarray:
    return np.dstack([art, np.full(art.shape[:2], 255, dtype=np.uint8)])


def clear_outer_white(rgba: np.ndarray) -> np.ndarray:
    height, width = rgba.shape[:2]
    is_white = (rgba[:, :, :3] >= WHITE_THRESHOLD).all(axis=2)
    seen = np.zeros_like(is_white)
    stack = [(y, x) for y in range(height) for x in (0, width - 1)]
    stack += [(y, x) for x in range(width) for y in (0, height - 1)]
    while stack:
        y, x = stack.pop()
        if not (0 <= y < height and 0 <= x < width) or seen[y, x] or not is_white[y, x]:
            continue
        seen[y, x] = True
        stack += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    result = rgba.copy()
    result[seen, 3] = 0
    return result


def save(rgba: np.ndarray, path: Path) -> None:
    image = Image.fromarray(rgba, "RGBA")
    factor = SCALE // TEXT_DENSITY
    image.resize((image.width * factor, image.height * factor), Image.NEAREST).save(path, optimize=True)
    print(f"{path.name}: README width {image.width * factor // 2}")


def build_banner(art: np.ndarray) -> np.ndarray:
    left, top, right, bottom = BANNER_BOX
    banner = refine(to_rgba(art[top:bottom, left:right]))
    draw_text(banner, "HELLO.EXE", 156, 24, WHITE)
    draw_text(banner, "NATAN VIANA", 192, 41, INK)
    draw_text(banner, "DEVELOPER", 192, 51, INK)
    draw_text(banner, "BRAZIL", 192, 61, (40, 90, 200))
    return banner


def build_taskbar(art: np.ndarray) -> np.ndarray:
    left, top, right, bottom = TASKBAR_BOX
    taskbar = refine(clear_outer_white(to_rgba(art[top:bottom, left:right])))
    draw_text(taskbar, "NATAN", 16, 10, WHITE)
    draw_text(taskbar, "UNCACHED.APP", 72, 10, WHITE)
    draw_text(taskbar, "UTC-3 BR", 364, 10, WHITE)
    return taskbar


def build_icon(art: np.ndarray, column: tuple, label: str) -> np.ndarray:
    top, bottom = ICON_ROW
    icon = clear_outer_white(to_rgba(art[top:bottom, column[0]:column[1]]))
    tile_width, tile_height = ICON_TILE
    tile = np.zeros((tile_height, tile_width, 4), dtype=np.uint8)
    x = (tile_width - icon.shape[1]) // 2
    tile[1:1 + icon.shape[0], x:x + icon.shape[1]] = icon
    tile = refine(tile)
    draw_label(tile, label)
    return tile


def main() -> None:
    sheet = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(float)
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    art = resample(sheet)
    save(build_banner(art), out / "banner.png")
    save(build_taskbar(art), out / "taskbar.png")
    for name, column, label in zip(ICON_NAMES, ICON_COLUMNS, ICON_LABELS):
        save(build_icon(art, column, label), out / f"icon-{name}.png")


if __name__ == "__main__":
    main()
