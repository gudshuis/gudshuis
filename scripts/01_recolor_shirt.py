"""Recolor the shirt to vibrant red using a hand-drawn spatial polygon (not
color clustering), so skin/sunglasses/hair stay untouched. Hue is replaced
but original Value/shading is kept so folds/highlights look natural on the
new color.

Usage: python 01_recolor_shirt.py <source.jpg> [out.png]
"""
import sys

import cv2
import numpy as np

# Polygon traced against assets/source-photo.jpg's shirt silhouette
# (coords in the full 1152x2048 source image).
POLY = [
    (470, 910), (670, 915), (710, 940), (800, 955), (835, 1090),
    (810, 1200), (440, 1220), (390, 1090), (420, 950), (475, 925),
]

RED_HUE = 3          # OpenCV hue 0-179; near-pure red
SAT_BOOST = 1.35


def build_mask(shape) -> np.ndarray:
    h, w = shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    pts = np.array(POLY, dtype=np.int32)
    cv2.fillPoly(mask, [pts], 255)
    mask = cv2.GaussianBlur(mask, (7, 7), 0)
    return mask


def recolor(img: np.ndarray) -> np.ndarray:
    mask = build_mask(img.shape).astype(np.float32) / 255.0

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    red_hsv = hsv.copy()
    red_hsv[:, :, 0] = RED_HUE
    red_hsv[:, :, 1] = np.clip(red_hsv[:, :, 1] * SAT_BOOST, 0, 255)
    red_bgr = cv2.cvtColor(red_hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)

    mask_3 = mask[:, :, None]
    out = img.astype(np.float32) * (1 - mask_3) + red_bgr * mask_3
    return out.astype(np.uint8)


if __name__ == "__main__":
    source = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "shirt-red.png"
    img = cv2.imread(source)
    result = recolor(img)
    cv2.imwrite(out, result)
    print(f"wrote {out}")
