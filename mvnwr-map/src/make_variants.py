"""Make delivery variants from the full-bleed print PDF.

  python make_variants.py ../output/MVNWR_wall_map_84x42in_FedEx.pdf

Writes, next to the input:
  *_trim-size_no-bleed.pdf   page cropped to the 84 x 42 in trim (for borderless printing on 42 in media)
  *_preview.jpg              a small preview image (about 2,500 px wide)
"""
from __future__ import annotations

import os
import subprocess
import sys

import pikepdf


def no_bleed(src: str, dst: str):
    pdf = pikepdf.open(src)
    page = pdf.pages[0]
    trim = page.obj.TrimBox
    x0, y0, x1, y1 = [float(v) for v in trim]
    # shift content so the trim corner becomes the page origin, then size the page to the trim
    w, h = x1 - x0, y1 - y0
    page.contents_add(pdf.make_stream(f"q 1 0 0 1 {-x0} {-y0} cm\n".encode()), prepend=True)
    page.contents_add(pdf.make_stream(b"\nQ\n"))
    for box in ("MediaBox", "CropBox", "BleedBox", "TrimBox"):
        page.obj[pikepdf.Name("/" + box)] = pikepdf.Array([0, 0, w, h])
    pdf.save(dst, object_stream_mode=pikepdf.ObjectStreamMode.disable, min_version="1.4")


def preview(src: str, dst: str, dpi: int = 30):
    stem = dst[: -len(".jpg")]
    subprocess.run(["pdftoppm", "-r", str(dpi), "-jpeg", "-jpegopt", "quality=88", "-singlefile", src, stem],
                   check=True)


if __name__ == "__main__":
    src = os.path.abspath(sys.argv[1])
    base = src[: -len(".pdf")]
    no_bleed(src, base + "_trim-size_no-bleed.pdf")
    preview(src, base + "_preview.jpg")
    print("wrote", base + "_trim-size_no-bleed.pdf", "and", base + "_preview.jpg")
