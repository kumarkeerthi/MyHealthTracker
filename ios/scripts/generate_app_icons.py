#!/usr/bin/env python3
"""Generate iOS AppIcon PNG files from the SVG design without external dependencies.

Outputs PNGs into:
  ios/MetabolicIntelligence/Resources/Assets.xcassets/AppIcon.appiconset
"""
from pathlib import Path
import struct
import zlib

OUT_DIR = Path(__file__).resolve().parents[1] / "MetabolicIntelligence/Resources/Assets.xcassets/AppIcon.appiconset"


def write_png(path: Path, w: int, h: int, pixels):
    raw = b""
    for y in range(h):
        raw += b"\x00" + bytes(pixels[y])
    comp = zlib.compress(raw, 9)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


def draw_disc(pix, w, h, cx, cy, r, color):
    rr = r * r
    for y in range(cy - r, cy + r + 1):
        if y < 0 or y >= h:
            continue
        for x in range(cx - r, cx + r + 1):
            if x < 0 or x >= w:
                continue
            if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= rr:
                i = x * 4
                pix[y][i : i + 4] = bytes(color)


def draw_thick_line(pix, w, h, a, b, color, thickness):
    x1, y1 = a
    x2, y2 = b
    steps = max(abs(x2 - x1), abs(y2 - y1), 1)
    for s in range(steps + 1):
        x = int(x1 + (x2 - x1) * s / steps)
        y = int(y1 + (y2 - y1) * s / steps)
        draw_disc(pix, w, h, x, y, thickness // 2, color)


def draw_polyline(pix, w, h, points, color, thickness):
    for a, b in zip(points, points[1:]):
        draw_thick_line(pix, w, h, a, b, color, thickness)


def draw_icon(px: int):
    w = h = px
    pix = [bytearray(w * 4) for _ in range(h)]

    # Dark subtle vertical gradient background.
    for y in range(h):
        t = y / (h - 1 if h > 1 else 1)
        r = int(14 + (21 - 14) * t)
        g = int(17 + (27 - 17) * t)
        b = int(22 + (34 - 22) * t)
        row = pix[y]
        for x in range(w):
            i = x * 4
            row[i : i + 4] = bytes((r, g, b, 255))

    emerald = (34, 230, 182, 255)

    # Shield stroke.
    shield_points = [(0.5, 0.18), (0.75, 0.285), (0.75, 0.48), (0.5, 0.83), (0.25, 0.48), (0.25, 0.285), (0.5, 0.18)]
    shield = [(int(x * w), int(y * h)) for x, y in shield_points]
    draw_polyline(pix, w, h, shield, emerald, max(1, px // 40))

    # Metabolic pulse line.
    pulse_points = [(0.31, 0.55), (0.42, 0.55), (0.48, 0.44), (0.54, 0.60), (0.60, 0.50), (0.69, 0.50)]
    pulse = [(int(x * w), int(y * h)) for x, y in pulse_points]
    draw_polyline(pix, w, h, pulse, emerald, max(1, px // 34))

    return pix


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sizes = [20, 29, 40, 58, 60, 76, 80, 87, 120, 152, 167, 180, 1024]
    for s in sizes:
        write_png(OUT_DIR / f"icon-{s}.png", s, s, draw_icon(s))
    print(f"Generated {len(sizes)} icon PNG files in {OUT_DIR}")


if __name__ == "__main__":
    main()
