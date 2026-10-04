"""Sheet geometry: trim, bleed, scale and the map-to-page transform."""
from __future__ import annotations

from dataclasses import dataclass

CRS = "EPSG:26915"          # NAD83 / UTM zone 15N


@dataclass(frozen=True)
class Frame:
    trim_w: float = 84.0     # inches (FedEx Office custom poster on a 42 in roll)
    trim_h: float = 42.0
    bleed: float = 0.125     # FedEx minimum bleed on all sides
    safe: float = 1.0        # keep type at least this far inside the trim
    scale: float = 42000.0   # 1:42,000
    cx: float = 456500.0     # map centre, UTM metres
    cy: float = 4950700.0

    @property
    def page_w(self):
        return self.trim_w + 2 * self.bleed

    @property
    def page_h(self):
        return self.trim_h + 2 * self.bleed

    @property
    def m_per_in(self):
        return self.scale * 0.0254

    @property
    def upp(self):
        """map metres per typographic point"""
        return self.m_per_in / 72.0

    @property
    def x0(self):
        return self.cx - self.page_w / 2 * self.m_per_in

    @property
    def x1(self):
        return self.cx + self.page_w / 2 * self.m_per_in

    @property
    def y0(self):
        return self.cy - self.page_h / 2 * self.m_per_in

    @property
    def y1(self):
        return self.cy + self.page_h / 2 * self.m_per_in

    @property
    def bounds(self):
        return self.x0, self.y0, self.x1, self.y1

    def to_map(self, x_in, y_in):
        """sheet inches (from sheet lower-left, bleed included) -> UTM metres"""
        return self.x0 + x_in * self.m_per_in, self.y0 + y_in * self.m_per_in

    def to_page(self, x_m, y_m):
        return (x_m - self.x0) / self.m_per_in, (y_m - self.y0) / self.m_per_in

    def trim_box(self):
        b = self.bleed
        return b, b, b + self.trim_w, b + self.trim_h

    def safe_box(self):
        b = self.bleed + self.safe
        return b, b, self.page_w - b, self.page_h - b
