"""Convert a prepped grayscale image into a single-hue Floyd-Steinberg dot
SVG (dark.svg or light.svg), with an intro animation of ~60 interleaved
random groups fading in over ~2s, scattered across the whole portrait
(not a wipe, not grouped by region).

Usage: python 03_make_dither_svg.py <prepped.png> <out.svg> <#hex-color>
"""
import sys
import random

import numpy as np
from PIL import Image

GRID_W, GRID_H = 300, 340
DOT = 1.0            # dot size in output units (before scale)
SCALE = 2.0           # output px per grid cell
N_GROUPS = 60
INTRO_SPAN = 2.0      # seconds over which groups start
GROUP_DUR = 1.2        # each dot's own fade-in duration
INTRO_TOTAL = 3.2


def dither(img: Image.Image, invert: bool = False) -> np.ndarray:
    """1-bit Floyd-Steinberg, serpentine order. Returns bool array, True = ink.

    invert=True: ink marks BRIGHT pixels instead of dark ones. Needed for
    dark mode, where the background has already been blacked out (alpha
    cleared to 0) and we want dots to draw the lit subject, not the empty
    background — otherwise the background (darkest value) gets treated as
    "ink" and the whole canvas fills in backwards.
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
            out[y, x] = new == 0.0  # dark pixel -> ink dot
            err = old - new
            nx = x + 1 if left_to_right else x - 1
            px = x - 1 if left_to_right else x + 1
            if 0 <= nx < GRID_W:
                arr[y, nx] += err * 7 / 16
            if 0 <= px < GRID_W and y + 1 < GRID_H:
                arr[y + 1, px] += err * 3 / 16
            if y + 1 < GRID_H:
                arr[y + 1, x] += err * 5 / 16
            if y + 1 < GRID_H and nx < GRID_W and nx >= 0:
                arr[y + 1, nx] += err * 1 / 16
    return out


def evenness_metric(dots: list, n_groups: int) -> float:
    """Std-dev of each group's mean spatial position, normalized. Low = scattered/even."""
    groups = [[] for _ in range(n_groups)]
    for i, (x, y) in enumerate(dots):
        groups[i % n_groups].append((x, y))
    centroids = np.array([
        np.mean(g, axis=0) if g else (0, 0) for g in groups
    ])
    overall = centroids.mean(axis=0)
    spread = np.mean(np.linalg.norm(centroids - overall, axis=1))
    diag = np.hypot(GRID_W, GRID_H)
    return spread / diag


def render(dots_mask: np.ndarray, out_path: str, color: str, animate: bool,
           bg=None) -> None:
    ys, xs = np.where(dots_mask)
    dots = list(zip(xs.tolist(), ys.tolist()))
    random.Random(42).shuffle(dots)

    width = GRID_W * SCALE
    height = GRID_H * SCALE

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
        f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}">',
    ]
    if bg:
        parts.append(f'<rect width="100%" height="100%" fill="{bg}"/>')

    # Duplicate layer note: for a real intro effect GitHub SMIL needs the
    # dots present twice (invisible base + animated copy) so nothing pops
    # before its animation begins; opacity:0 initial state covers this here.
    if animate:
        delays = [random.Random(1).uniform(0, INTRO_SPAN) for _ in dots]
        # Interleave: assign delay by (index mod N_GROUPS) bucket, jittered,
        # so groups are scattered across the whole portrait, not by region.
        for gi in range(N_GROUPS):
            group_delay = (gi / N_GROUPS) * INTRO_SPAN
            for i in range(gi, len(dots), N_GROUPS):
                delays[i] = group_delay + random.Random(i).uniform(-0.05, 0.05)

        path_by_delay: dict = {}
        for (x, y), d in zip(dots, delays):
            key = round(d, 3)
            path_by_delay.setdefault(key, []).append((x, y))

        parts.append(f'<style>path {{ fill: {color}; }}</style>')
        for delay, pts in sorted(path_by_delay.items()):
            d_attr = "".join(
                f"M{x*SCALE:.1f} {y*SCALE:.1f}h{DOT*SCALE:.1f}v{DOT*SCALE:.1f}h-{DOT*SCALE:.1f}Z"
                for x, y in pts
            )
            parts.append(
                f'<path d="{d_attr}" shape-rendering="crispEdges" opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{max(delay,0):.3f}s" dur="{GROUP_DUR}s" fill="freeze"/>'
                f'</path>'
            )
    else:
        parts.append(f'<style>path {{ fill: {color}; }}</style>')
        d_attr = "".join(
            f"M{x*SCALE:.1f} {y*SCALE:.1f}h{DOT*SCALE:.1f}v{DOT*SCALE:.1f}h-{DOT*SCALE:.1f}Z"
            for x, y in dots
        )
        parts.append(f'<path d="{d_attr}" shape-rendering="crispEdges"/>')

    parts.append("</svg>")
    with open(out_path, "w") as f:
        f.write("\n".join(parts))

    ev = evenness_metric(dots, N_GROUPS)
    print(f"wrote {out_path} ({len(dots)} dots, this-script's evenness proxy={ev:.3f} "
          f"[lower = groups more scattered across whole portrait, not a spatial patch]. "
          f"Not the master prompt's exact metric — that algorithm wasn't specified, "
          f"this is a stand-in; judge the real result visually in a browser.)")


if __name__ == "__main__":
    src, out, color = sys.argv[1], sys.argv[2], sys.argv[3]
    static = "--static" in sys.argv
    invert = "--invert" in sys.argv
    bg = "#0A101F" if invert else None  # dark-mode panel background
    img = Image.open(src)
    mask = dither(img, invert=invert)
    render(mask, out, color, animate=not static, bg=bg)
