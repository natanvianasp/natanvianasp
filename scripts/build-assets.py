"""Builds the profile assets from a Google Flow pixel-art sheet.

Usage: python build-assets.py <sheet.jpg> <out-dir>

The sheet is resampled onto its native pixel grid (STEP source pixels per art
pixel, phase OFFSET_X/OFFSET_Y), reduced to PALETTE_SIZE colours, cut into its
items, labelled with a 3x5 bitmap font on the same grid, and written at SCALE
device pixels per art pixel. README widths are art width * SCALE / 2 so retina
screens get exact integer scaling.
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

STEP, OFFSET_X, OFFSET_Y = 5.74, 0.0, 2.8
PALETTE_SIZE = 64
SCALE = 8
WHITE_THRESHOLD = 235

BANNER_BOX = (13, 10, 227, 59)
TASKBAR_BOX = (10, 111, 230, 125)
ICON_ROW = (73, 99)
ICON_COLUMNS = ((15, 36), (51, 76), (89, 113), (128, 149), (164, 189), (202, 227))
ICON_NAMES = ("uncached", "core", "desktop", "website", "portfolio", "ri7")
ICON_LABELS = ("UNCACHED", "CORE", "DESKTOP", "WEBSITE", "PORTFOLIO", "RI7")
ICON_TILE = (40, 37)

INK = (20, 20, 15)
WHITE = (255, 255, 255)

GLYPHS = {
    "A": "010101111101101", "B": "110101110101110", "C": "011100100100011",
    "D": "110101101101110", "E": "111100110100111", "F": "111100110100100",
    "G": "011100101101011", "H": "101101111101101", "I": "111010010010111",
    "K": "101101110101101", "L": "100100100100111", "M": "101111111101101",
    "N": "110101101101101", "O": "010101101101010", "P": "110101110100100",
    "R": "110101110101101", "S": "011100010001110", "T": "111010010010010",
    "U": "101101101101111", "V": "101101101101010", "W": "101101111111101",
    "X": "101101010101101", "Y": "101101010010010", "Z": "111001010100111",
    "0": "111101101101111", "1": "010110010010111", "2": "110001010100111",
    "3": "110001010001110", "4": "101101111001001", "5": "111100110001110",
    "7": "111001010010010", "-": "000000111000000", ".": "000000000000010",
    "!": "010010010000010", " ": "000000000000000", ":": "000010000010000",
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
    return len(text) * 4 - 1


def draw_text(canvas: np.ndarray, text: str, x: int, y: int, color) -> None:
    for index, char in enumerate(text):
        for bit_index, bit in enumerate(GLYPHS[char]):
            if bit == "1":
                canvas[y + bit_index // 3, x + index * 4 + bit_index % 3] = (*color, 255)


def draw_label(tile: np.ndarray, label: str) -> None:
    """Ink-bordered white tag across the bottom 8 rows, readable on light and dark themes."""
    width = text_width(label) + 4
    left = (tile.shape[1] - width) // 2
    top = tile.shape[0] - 8
    tile[top:top + 7, left:left + width] = (*INK, 255)
    tile[top + 1:top + 6, left + 1:left + width - 1] = (*WHITE, 255)
    draw_text(tile, label, left + 2, top + 1, INK)


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
    image.resize((image.width * SCALE, image.height * SCALE), Image.NEAREST).save(path, optimize=True)
    print(f"{path.name}: art {image.width}x{image.height}, README width {image.width * SCALE // 2}")


def build_banner(art: np.ndarray) -> np.ndarray:
    left, top, right, bottom = BANNER_BOX
    banner = to_rgba(art[top:bottom, left:right])
    draw_text(banner, "HELLO.EXE", 78, 11, WHITE)
    draw_text(banner, "NATAN", 96, 19, INK)
    draw_text(banner, "VIANA", 96, 25, INK)
    draw_text(banner, "DEV - BR", 96, 31, (40, 90, 200))
    return banner


def build_taskbar(art: np.ndarray) -> np.ndarray:
    left, top, right, bottom = TASKBAR_BOX
    taskbar = clear_outer_white(to_rgba(art[top:bottom, left:right]))
    draw_text(taskbar, "NATAN", 8, 5, WHITE)
    draw_text(taskbar, "UTC-3 BR", 178, 5, WHITE)
    return taskbar


def build_icon(art: np.ndarray, column: tuple, label: str) -> np.ndarray:
    top, bottom = ICON_ROW
    icon = clear_outer_white(to_rgba(art[top:bottom, column[0]:column[1]]))
    tile_width, tile_height = ICON_TILE
    tile = np.zeros((tile_height, tile_width, 4), dtype=np.uint8)
    x = (tile_width - icon.shape[1]) // 2
    tile[1:1 + icon.shape[0], x:x + icon.shape[1]] = icon
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
