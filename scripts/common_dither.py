"""Shared Floyd-Steinberg dither + dot-group logic, used by both the
standalone portrait preview script and the full banner builder.
"""
import random

import numpy as np
from PIL import Image

GRID_W, GRID_H = 300, 340


def dither(img: Image.Image, invert: bool = False) -> np.ndarray:
    """1-bit Floyd-Steinberg, serpentine order. Returns bool array, True = ink.

    invert=True: ink marks BRIGHT pixels instead of dark ones (dark mode,
    where background is already blacked out and dots should draw the lit
    subject, not the empty background).
    """
    small = img.convert("L").resize((GRID_W, GRID_H), Image.LANCZOS)
    arr = np.array(small, dtype=np.float64)
    if invert:
        arr = 255.0 - arr
    out = np.zeros((GRID_H, GRID_W), dtype=bool)

    for y in range(GRID_H):
        left_to_right = (y % 2 == 0)
        xs = range(GRID_W) if left_to_right else range(GRID_W - 1, -1, -1)
        for x in xs:
            old = arr[y, x]
            new = 0.0 if old < 128 else 255.0
            out[y, x] = new == 0.0
            err = old - new
            nx = x + 1 if left_to_right else x - 1
            px = x - 1 if left_to_right else x + 1
            if 0 <= nx < GRID_W:
                arr[y, nx] += err * 7 / 16
            if 0 <= px < GRID_W and y + 1 < GRID_H:
                arr[y + 1, px] += err * 3 / 16
            if y + 1 < GRID_H:
                arr[y + 1, x] += err * 5 / 16
            if y + 1 < GRID_H and 0 <= nx < GRID_W:
                arr[y + 1, nx] += err * 1 / 16
    return out


def dots_from_mask(mask: np.ndarray, seed: int = 42):
    ys, xs = np.where(mask)
    dots = list(zip(xs.tolist(), ys.tolist()))
    random.Random(seed).shuffle(dots)
    return dots
