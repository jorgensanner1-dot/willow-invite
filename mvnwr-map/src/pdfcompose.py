"""Assemble the print PDF: an opaque JPEG base raster plus a vector overlay.

The base raster (background colour, terrain shading, land tints) is embedded
as a DCT (JPEG) image so the file stays a manageable size; everything else
(water, lines, outlines, type) stays vector.  Nothing in the final page uses
transparency groups at the page level, which keeps RIP software happy.
"""
from __future__ import annotations

import pikepdf
from pikepdf import Name, Dictionary, Array


def compose(jpeg_path: str, overlay_pdf: str, out_pdf: str, page_w_in: float, page_h_in: float,
            bleed_in: float, bg_rgb=(0.949, 0.918, 0.847), title: str = "", author: str = "",
            subject: str = "", keywords: str = ""):
    W, H = page_w_in * 72.0, page_h_in * 72.0
    pdf = pikepdf.new()
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    with Image.open(jpeg_path) as im:
        iw, ih = im.size
        mode = im.mode
    data = open(jpeg_path, "rb").read()
    from PIL import ImageCms
    import os
    icc_path = os.path.join(os.path.dirname(pikepdf.__file__), "pdfa", "data", "sRGB.icc")  # ICC v2 sRGB
    icc = pdf.make_stream(open(icc_path, "rb").read())
    icc.N = 3
    icc.Alternate = Name.DeviceRGB
    cs = Array([Name.ICCBased, icc])
    img = pikepdf.Stream(pdf, data)
    img.Type = Name.XObject
    img.Subtype = Name.Image
    img.Width = iw
    img.Height = ih
    img.ColorSpace = cs if mode == "RGB" else Name.DeviceCMYK
    img.BitsPerComponent = 8
    img.Filter = Name.DCTDecode

    r, g, b = bg_rgb
    content = (f"q {r:.4f} {g:.4f} {b:.4f} rg 0 0 {W:.3f} {H:.3f} re f Q\n"
               f"q {W:.3f} 0 0 {H:.3f} 0 0 cm /Im0 Do Q\n").encode()
    page = pikepdf.Page(pdf.add_blank_page(page_size=(W, H)))
    page.obj.Resources = Dictionary(XObject=Dictionary(Im0=img), ColorSpace=Dictionary(DefaultRGB=cs))
    page.obj.Contents = pdf.make_stream(content)

    over = pikepdf.open(overlay_pdf)
    page.add_overlay(over.pages[0])
    # tag the overlay form with sRGB and neutralise zero-alpha graphics states (nothing is composited)
    for name, xo in page.obj.Resources.XObject.items():
        if xo.get("/Subtype") != Name.Form:
            continue
        res = xo.get("/Resources")
        if res is None:
            continue
        res.ColorSpace = Dictionary(DefaultRGB=cs)
        egs = res.get("/ExtGState")
        if egs is not None:
            for k in list(egs.keys()):
                gs = egs[k]
                if float(gs.get("/CA", 1)) == 0:
                    gs.CA = 1
                if float(gs.get("/ca", 1)) == 0:
                    gs.ca = 1

    b = bleed_in * 72.0
    page.obj.MediaBox = Array([0, 0, W, H])
    page.obj.BleedBox = Array([0, 0, W, H])
    page.obj.TrimBox = Array([b, b, W - b, H - b])
    page.obj.CropBox = Array([0, 0, W, H])

    with pdf.open_metadata() as meta:
        meta["dc:title"] = title
        meta["dc:creator"] = [author] if author else []
        meta["dc:description"] = subject
        meta["pdf:Keywords"] = keywords
    pdf.docinfo["/Title"] = title
    pdf.docinfo["/Subject"] = subject
    pdf.docinfo["/Keywords"] = keywords
    if author:
        pdf.docinfo["/Author"] = author
    pdf.save(out_pdf, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.disable, min_version="1.4")
