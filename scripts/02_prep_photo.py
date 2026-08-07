"""Crop to head+shoulders, then prep for the dot-dither pipeline per the
master prompt: background segmentation (dark mode), autocontrast(cutoff=1),
UnsharpMask(radius=3, percent=140).

Outputs:
  prepped-dark.png  - subject only, background removed (transparent -> black)
  prepped-light.png - full crop, background kept

Usage: python 02_prep_photo.py <source.png>
"""
import sys
import io

import numpy as np
from PIL import Image, ImageOps, ImageFilter
from rembg import remove

# Head+shoulders crop, hand-picked against source-red-shirt.png (1152x2048).
CROP_BOX = (300, 600, 760, 1220)  # x0, y0, x1, y1


def prep(source_path: str) -> None:
    img = Image.open(source_path).convert("RGB")
    crop = img.crop(CROP_BOX)
    crop.save("prepped-crop.png")

    # ---- Light mode: keep background ----
    light = ImageOps.autocontrast(crop.convert("L"), cutoff=1)
    light = light.filter(ImageFilter.UnsharpMask(radius=3, percent=140))
    light.save("prepped-light.png")

    # ---- Dark mode: segment subject out ----
    buf = io.BytesIO()
    crop.save(buf, format="PNG")
    cutout = remove(buf.getvalue())
    rgba = Image.open(io.BytesIO(cutout)).convert("RGBA")

    alpha = np.array(rgba)[:, :, 3]
    gray = np.array(rgba.convert("L"))
    # Hard-clear anti-aliased edge bleed from the cutout mask.
    gray = np.where(alpha > 40, gray, 0).astype(np.uint8)

    dark = Image.fromarray(gray)
    dark = ImageOps.autocontrast(dark, cutoff=1)
    dark = dark.filter(ImageFilter.UnsharpMask(radius=3, percent=140))
    # Re-clear background after unsharp (halos can leak past mask edge).
    dark_arr = np.where(alpha > 40, np.array(dark), 0).astype(np.uint8)
    Image.fromarray(dark_arr).save("prepped-dark.png")

    print("wrote prepped-crop.png, prepped-light.png, prepped-dark.png")


if __name__ == "__main__":
    prep(sys.argv[1])
