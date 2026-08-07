"""mcp.webp has a baked-in solid white background (no alpha channel), which
shows as a white box when crossfaded over the dark banner. Key out
near-white pixels to transparent so it composites cleanly on both themes.

Usage: python 05_fix_mcp_logo.py <source.webp> <out.png>
"""
import sys

import numpy as np
from PIL import Image

WHITE_THRESHOLD = 235


def fix(source_path: str, out_path: str) -> None:
    img = Image.open(source_path).convert("RGB")
    arr = np.array(img)
    is_white = np.all(arr > WHITE_THRESHOLD, axis=-1)
    alpha = np.where(is_white, 0, 255).astype(np.uint8)
    rgba = np.dstack([arr, alpha])
    Image.fromarray(rgba, mode="RGBA").save(out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    fix(sys.argv[1], sys.argv[2])
