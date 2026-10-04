"""Cartographic helpers for the Minnesota Valley NWR wall map.

Everything here works in two coordinate systems:
  * map axes: data units are metres in NAD83 / UTM zone 15N (EPSG:26915)
  * page axes: data units are inches measured from the lower-left corner of
    the full sheet (bleed included)
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import matplotlib.patheffects as pe
from matplotlib.font_manager import FontProperties
from matplotlib.patches import PathPatch, FancyBboxPatch, Polygon as MplPolygon
from matplotlib.path import Path
from matplotlib.textpath import text_to_path


# --------------------------------------------------------------------------
# fonts
# --------------------------------------------------------------------------
class Fonts:
    def __init__(self, font_dir: str):
        self.dir = font_dir.rstrip("/") + "/"

    def serif(self, weight=400, italic=False):
        return FontProperties(fname=f"{self.dir}EBGaramond-{weight}{'Italic' if italic else ''}.ttf")

    def sans(self, weight=400, italic=False):
        return FontProperties(fname=f"{self.dir}SourceSans3-{weight}{'Italic' if italic else ''}.ttf")


def _sized(fp: FontProperties, size: float) -> FontProperties:
    f = fp.copy()
    f.set_size(size)
    return f


def text_width_pt(text: str, fp: FontProperties, size: float) -> float:
    if not text:
        return 0.0
    w, _, _ = text_to_path.get_text_width_height_descent(text, _sized(fp, size), ismath=False)
    return w


def advances_pt(text: str, fp: FontProperties, size: float) -> list[float]:
    """Per-character advance widths (kerning folded in via prefix differences)."""
    out, prev = [], 0.0
    for i in range(1, len(text) + 1):
        w = text_width_pt(text[:i], fp, size)
        out.append(w - prev)
        prev = w
    return out


def halo(width_pt: float, color: str):
    return [pe.withStroke(linewidth=width_pt, foreground=color, capstyle="round", joinstyle="round")]


# --------------------------------------------------------------------------
# letter-spaced straight text
# --------------------------------------------------------------------------
def spaced_text(ax, x, y, text, fp, size, *, tracking=0.0, color="k", ha="center", va="baseline",
                rotation=0.0, units_per_pt=1.0, halo_w=0.0, halo_color="#F2EAD8", zorder=50,
                alpha=1.0):
    """Draw text with extra letter spacing (tracking in em).

    units_per_pt converts points to axes data units (1/72 for page axes in
    inches, metres-per-point for the map axes).
    """
    adv = advances_pt(text, fp, size)
    track = tracking * size
    total = sum(adv) + track * (len(text) - 1)
    ang = math.radians(rotation)
    ux, uy = math.cos(ang), math.sin(ang)
    vx, vy = -uy, ux
    if ha == "center":
        s = -total / 2
    elif ha == "right":
        s = -total
    else:
        s = 0.0
    # vertical anchor: use cap height approximation
    _, h, d = text_to_path.get_text_width_height_descent("H", _sized(fp, size), ismath=False)
    if va == "center":
        voff = -h / 2
    elif va == "top":
        voff = -h
    elif va == "bottom":
        voff = d
    else:
        voff = 0.0
    effects = halo(halo_w, halo_color) if halo_w else None
    arts = []
    for ch, a in zip(text, adv):
        cx = s + a / 2
        px = x + (cx * ux + voff * vx) * units_per_pt
        py = y + (cx * uy + voff * vy) * units_per_pt
        if ch != " ":
            t = ax.text(px, py, ch, fontproperties=fp, fontsize=size, color=color, ha="center",
                        va="baseline", rotation=rotation, rotation_mode="anchor", zorder=zorder,
                        alpha=alpha, path_effects=effects)
            arts.append(t)
        s += a + track
    return total * units_per_pt


# --------------------------------------------------------------------------
# text along a curve
# --------------------------------------------------------------------------
def _resample_line(xy: np.ndarray, step: float) -> np.ndarray:
    seg = np.hypot(*np.diff(xy, axis=0).T)
    d = np.concatenate([[0], np.cumsum(seg)])
    n = max(2, int(d[-1] / step) + 1)
    t = np.linspace(0, d[-1], n)
    return np.column_stack([np.interp(t, d, xy[:, 0]), np.interp(t, d, xy[:, 1])])


def _smooth_line(xy: np.ndarray, window: int) -> np.ndarray:
    if window < 3 or len(xy) < window:
        return xy
    k = np.ones(window) / window
    pad = window // 2
    xp = np.pad(xy[:, 0], pad, mode="edge")
    yp = np.pad(xy[:, 1], pad, mode="edge")
    return np.column_stack([np.convolve(xp, k, "valid")[: len(xy)], np.convolve(yp, k, "valid")[: len(xy)]])


def text_on_path(ax, line_xy, text, fp, size, *, units_per_pt, tracking=0.0, color="k", at=0.5,
                 offset_pt=0.0, halo_w=0.0, halo_color="#F2EAD8", zorder=50, smooth_pt=40.0,
                 keep_upright=True, valign="center"):
    """Place characters of `text` along a polyline (map units), centred at fraction `at`.

    smooth_pt: window (in points) used to smooth the baseline so letters don't
    jitter on wiggly rivers.  offset_pt shifts the baseline perpendicular to the
    line (positive = left of travel direction, i.e. above the text).
    Returns the list of text artists.
    """
    xy = np.asarray(line_xy, dtype=float)
    step = max(units_per_pt * 2.0, 1e-9)
    xy = _resample_line(xy, step)
    xy = _smooth_line(xy, int(smooth_pt * units_per_pt / step) | 1)
    if keep_upright:
        mid = len(xy) // 2
        i0, i1 = max(0, mid - 5), min(len(xy) - 1, mid + 5)
        if xy[i1, 0] < xy[i0, 0]:
            xy = xy[::-1]
            at = 1 - at
    seg = np.hypot(*np.diff(xy, axis=0).T)
    d = np.concatenate([[0], np.cumsum(seg)])
    L = d[-1]
    adv = advances_pt(text, fp, size)
    track = tracking * size
    total = (sum(adv) + track * (len(text) - 1)) * units_per_pt
    s = at * L - total / 2
    _, h, _ = text_to_path.get_text_width_height_descent("x", _sized(fp, size), ismath=False)
    voff = -h / 2 if valign == "center" else 0.0
    effects = halo(halo_w, halo_color) if halo_w else None
    arts = []
    for ch, a in zip(text, adv):
        a_m = a * units_per_pt
        c = s + a_m / 2
        if ch != " ":
            c0, c1 = np.clip([c - a_m / 2 - 1e-6, c + a_m / 2 + 1e-6], 0, L)
            x0, y0 = np.interp(c0, d, xy[:, 0]), np.interp(c0, d, xy[:, 1])
            x1, y1 = np.interp(c1, d, xy[:, 0]), np.interp(c1, d, xy[:, 1])
            ang = math.atan2(y1 - y0, x1 - x0)
            cx, cy = np.interp(np.clip(c, 0, L), d, xy[:, 0]), np.interp(np.clip(c, 0, L), d, xy[:, 1])
            nx, ny = -math.sin(ang), math.cos(ang)
            off = (offset_pt + voff) * units_per_pt
            t = ax.text(cx + nx * off, cy + ny * off, ch, fontproperties=fp, fontsize=size, color=color,
                        ha="center", va="baseline", rotation=math.degrees(ang), rotation_mode="anchor",
                        zorder=zorder, path_effects=effects)
            arts.append(t)
        s += a_m + track * units_per_pt
    return arts


# --------------------------------------------------------------------------
# highway shields (drawn in map units, sized in points)
# --------------------------------------------------------------------------
def _interstate_path():
    # unit shield roughly 1 wide x 1 tall, centred at 0,0
    verts = [(-0.50, 0.42), (-0.25, 0.50), (0.0, 0.44), (0.25, 0.50), (0.50, 0.42),
             (0.50, 0.05), (0.46, -0.20), (0.30, -0.38), (0.0, -0.50), (-0.30, -0.38),
             (-0.46, -0.20), (-0.50, 0.05), (-0.50, 0.42)]
    return verts


def _us_path():
    verts = [(-0.46, 0.50), (0.46, 0.50), (0.44, 0.18), (0.48, -0.05), (0.40, -0.28),
             (0.20, -0.42), (0.0, -0.50), (-0.20, -0.42), (-0.40, -0.28), (-0.48, -0.05),
             (-0.44, 0.18), (-0.46, 0.50)]
    return verts


@dataclass
class ShieldStyle:
    interstate_body: str = "#3F5F7E"
    interstate_top: str = "#9E4B3C"
    us_body: str = "#FFFDF7"
    state_body: str = "#FFFDF7"
    county_body: str = "#E9DCC3"
    outline: str = "#3B3631"
    text_dark: str = "#2E2A26"
    text_light: str = "#FFFFFF"


def draw_shield(ax, x, y, kind, number, fonts: Fonts, *, units_per_pt, size_pt=16.0,
                style: ShieldStyle = ShieldStyle(), zorder=80):
    """kind in {'I','US','MN','CR'}; size_pt = shield height in points."""
    num = str(number)
    s = size_pt * units_per_pt
    digits = len(num)
    fpb = fonts.sans(700)
    if kind == "I":
        wf = 1.0 if digits <= 2 else 1.22
        verts = [(x + vx * s * wf, y + vy * s) for vx, vy in _interstate_path()]
        ax.add_patch(MplPolygon(verts, closed=True, fc=style.interstate_body, ec="white",
                                lw=size_pt * 0.07, zorder=zorder, joinstyle="round"))
        ax.add_patch(MplPolygon(verts, closed=True, fc="none", ec=style.outline,
                                lw=size_pt * 0.035, zorder=zorder + 0.2, joinstyle="round"))
        top = [(x + vx * s * wf, y + vy * s) for vx, vy in
               [(-0.50, 0.42), (-0.25, 0.50), (0.0, 0.44), (0.25, 0.50), (0.50, 0.42), (0.50, 0.24), (-0.50, 0.24)]]
        ax.add_patch(MplPolygon(top, closed=True, fc=style.interstate_top, ec="none", zorder=zorder + 0.1))
        ax.text(x, y - 0.10 * s, num, fontproperties=fpb, fontsize=size_pt * (0.52 if digits <= 2 else 0.46),
                color=style.text_light, ha="center", va="center", zorder=zorder + 0.3)
    elif kind == "US":
        wf = 1.0 if digits <= 2 else 1.2
        verts = [(x + vx * s * wf, y + vy * s) for vx, vy in _us_path()]
        ax.add_patch(MplPolygon(verts, closed=True, fc=style.us_body, ec=style.outline,
                                lw=size_pt * 0.06, zorder=zorder, joinstyle="round"))
        ax.text(x, y + 0.02 * s, num, fontproperties=fpb, fontsize=size_pt * (0.55 if digits <= 2 else 0.48),
                color=style.text_dark, ha="center", va="center", zorder=zorder + 0.3)
    else:
        # state trunk highway / county road: rounded rectangle
        wf = {1: 0.95, 2: 1.05, 3: 1.35}.get(digits, 1.5)
        fc = style.state_body if kind == "MN" else style.county_body
        h = s * 0.82
        w = s * wf
        box = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                             boxstyle=f"round,pad=0,rounding_size={h * 0.32}",
                             fc=fc, ec=style.outline, lw=size_pt * 0.055, zorder=zorder)
        ax.add_patch(box)
        ax.text(x, y - 0.01 * s, num, fontproperties=fpb, fontsize=size_pt * 0.50,
                color=style.text_dark, ha="center", va="center", zorder=zorder + 0.3)


# --------------------------------------------------------------------------
# point symbols
# --------------------------------------------------------------------------
def star_path(n=5, inner=0.45):
    pts = []
    for i in range(2 * n):
        r = 1.0 if i % 2 == 0 else inner
        a = math.pi / 2 + i * math.pi / n
        pts.append((r * math.cos(a), r * math.sin(a)))
    pts.append(pts[0])
    return Path(pts, closed=True)


def polyline_length(xy):
    xy = np.asarray(xy)
    return float(np.hypot(*np.diff(xy, axis=0).T).sum())


def point_along(xy, frac):
    xy = np.asarray(xy, dtype=float)
    seg = np.hypot(*np.diff(xy, axis=0).T)
    d = np.concatenate([[0], np.cumsum(seg)])
    t = frac * d[-1]
    return float(np.interp(t, d, xy[:, 0])), float(np.interp(t, d, xy[:, 1]))
