"""Geometry -> matplotlib helpers (shapely geometries in map units)."""
from __future__ import annotations

import numpy as np
from matplotlib.collections import LineCollection, PathCollection
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from shapely.geometry import (LineString, MultiLineString, Polygon, MultiPolygon, GeometryCollection,
                              Point, MultiPoint)


def iter_lines(geoms):
    for g in geoms:
        if g is None or g.is_empty:
            continue
        if isinstance(g, LineString):
            yield g
        elif isinstance(g, (MultiLineString, GeometryCollection)):
            for p in g.geoms:
                yield from iter_lines([p])
        elif isinstance(g, (Polygon, MultiPolygon)):
            for p in iter_polys([g]):
                yield LineString(p.exterior.coords)
                for r in p.interiors:
                    yield LineString(r.coords)


def iter_polys(geoms):
    for g in geoms:
        if g is None or g.is_empty:
            continue
        if isinstance(g, Polygon):
            yield g
        elif isinstance(g, (MultiPolygon, GeometryCollection)):
            for p in g.geoms:
                yield from iter_polys([p])


def lines(ax, geoms, *, color, lw, zorder, ls="solid", capstyle="round", joinstyle="round", alpha=1.0,
          dashes=None):
    segs = [np.asarray(l.coords)[:, :2] for l in iter_lines(geoms)]
    if not segs:
        return None
    lc = LineCollection(segs, colors=color, linewidths=lw, zorder=zorder, alpha=alpha,
                        capstyle=capstyle, joinstyle=joinstyle)
    if dashes is not None:
        lc.set_linestyle((0, dashes))
    elif ls != "solid":
        lc.set_linestyle(ls)
    ax.add_collection(lc)
    return lc


def poly_path(p: Polygon) -> Path:
    verts, codes = [], []
    for ring in [p.exterior, *p.interiors]:
        c = np.asarray(ring.coords)[:, :2]
        if len(c) < 3:
            continue
        verts.append(c)
        cd = np.full(len(c), Path.LINETO, dtype=np.uint8)
        cd[0] = Path.MOVETO
        cd[-1] = Path.CLOSEPOLY
        codes.append(cd)
    if not verts:
        return None
    return Path(np.concatenate(verts), np.concatenate(codes))


def polys(ax, geoms, *, fc="none", ec="none", lw=0.0, zorder=10, alpha=1.0, ls="solid", hatch=None,
          joinstyle="round", dashes=None, simplify=2.0):
    if simplify:
        geoms = [g.simplify(simplify, preserve_topology=True) for g in geoms if g is not None]
    paths = [poly_path(p) for p in iter_polys(geoms)]
    paths = [p for p in paths if p is not None]
    if not paths:
        return None
    path = Path.make_compound_path(*paths)
    patch = PathPatch(path, fc=fc, ec=ec, lw=lw, zorder=zorder, alpha=alpha, hatch=hatch,
                      joinstyle=joinstyle)
    if dashes is not None:
        patch.set_linestyle((0, dashes))
    elif ls != "solid":
        patch.set_linestyle(ls)
    ax.add_patch(patch)
    return patch


def longest_line(geom):
    ls = list(iter_lines([geom]))
    return max(ls, key=lambda l: l.length) if ls else None
