#!/usr/bin/env python3
"""List dark neutral connected components inside an image search box."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("box", nargs=4, type=int, metavar=("X1", "Y1", "X2", "Y2"))
    parser.add_argument("--minimum-pixels", type=int, default=3)
    args = parser.parse_args()
    x1, y1, x2, y2 = args.box
    rgb = np.asarray(Image.open(args.image).convert("RGB"))[y1:y2, x1:x2]
    dark = (rgb.max(axis=2) < 145) & ((rgb.max(axis=2) - rgb.min(axis=2)) < 28)
    labels, count = ndimage.label(dark)
    objects = ndimage.find_objects(labels)
    found = []
    for index, slices in enumerate(objects, start=1):
        if slices is None:
            continue
        pixels = int((labels[slices] == index).sum())
        if pixels < args.minimum_pixels:
            continue
        ys, xs = slices
        found.append((x1 + xs.start, y1 + ys.start, x1 + xs.stop, y1 + ys.stop, pixels))
    for item in sorted(found, key=lambda value: (value[1], value[0])):
        print(*item)


if __name__ == "__main__":
    main()
