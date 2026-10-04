"""Terrain shading and raster compositing for the base layer."""
from __future__ import annotations

import numpy as np
from scipy import ndimage


def hillshade(z: np.ndarray, cell: float, az_deg: float, alt_deg: float, zf: float = 1.0) -> np.ndarray:
    """Lambertian hillshade, 0..1.  Row 0 of `z` is the north edge."""
    dzdx = ndimage.sobel(z, axis=1, mode="nearest") / (8.0 * cell)
    dzdy = ndimage.sobel(z, axis=0, mode="nearest") / (8.0 * cell)
    p = dzdx * zf          # rise toward east
    q = -dzdy * zf         # rise toward north
    az, alt = np.radians(az_deg), np.radians(alt_deg)
    lx, ly, lz = np.sin(az) * np.cos(alt), np.cos(az) * np.cos(alt), np.sin(alt)
    hs = (-p * lx - q * ly + lz) / np.sqrt(p * p + q * q + 1.0)
    return np.clip(hs, 0.0, 1.0)


def relative_shade(z, cell, lights=((315, 0.55), (270, 0.15), (0, 0.15), (225, 0.15)), alt_deg=40.0, zf=1.0):
    """Weighted multi-directional hillshade normalised so flat ground == 1.0."""
    tot = np.zeros(z.shape, dtype=np.float32)
    wsum = 0.0
    for az, w in lights:
        tot += (w * hillshade(z, cell, az, alt_deg, zf)).astype(np.float32)
        wsum += w
    flat = np.sin(np.radians(alt_deg))
    return tot / (wsum * flat)


def hex_rgb(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32) / 255.0


def apply_shade(rgb: np.ndarray, s: np.ndarray, *, shadow_tint="#6E6253", k_shadow=0.85,
                highlight="#FFFDF6", k_high=0.55, gamma_dark=1.0) -> np.ndarray:
    """Coloured-multiply shading.

    rgb: H x W x 3 float (0-1); s: relative shade (1 = flat, <1 shadow, >1 lit).
    Shadows multiply toward `shadow_tint` (keeps the hue of tints underneath);
    lit slopes lighten toward `highlight`.
    """
    dark = np.clip(1.0 - s, 0.0, 1.0) ** gamma_dark * k_shadow
    lit = np.clip(s - 1.0, 0.0, 1.0) * k_high
    tint = hex_rgb(shadow_tint)
    mult = 1.0 - dark[..., None] * (1.0 - tint[None, None, :])
    out = rgb * mult
    hi = hex_rgb(highlight)
    out = out * (1.0 - lit[..., None]) + hi[None, None, :] * lit[..., None]
    return np.clip(out, 0.0, 1.0)


def blend_mask(rgb: np.ndarray, mask: np.ndarray, color: str, opacity: float = 1.0) -> np.ndarray:
    """Paint `color` into rgb where mask (0..1 float or bool) is set."""
    c = hex_rgb(color)
    a = (mask.astype(np.float32) * opacity)[..., None]
    return rgb * (1.0 - a) + c[None, None, :] * a


def multiply_mask(rgb: np.ndarray, mask: np.ndarray, color: str, opacity: float = 1.0) -> np.ndarray:
    c = hex_rgb(color)
    a = (mask.astype(np.float32) * opacity)[..., None]
    return rgb * (1.0 - a + a * c[None, None, :])
