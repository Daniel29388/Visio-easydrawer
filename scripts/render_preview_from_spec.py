#!/usr/bin/env python
"""Render a PNG preview from a generic Visio figure JSON spec."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def font(size: float, bold: bool = False, italic: bool = False, family: str = "Times New Roman"):
    font_dir = Path(r"C:\Windows\Fonts")
    candidates = []
    if "times" in family.lower():
        candidates += ["timesbi.ttf"] if bold and italic else []
        candidates += ["timesbd.ttf"] if bold else []
        candidates += ["timesi.ttf"] if italic else []
        candidates += ["times.ttf"]
    candidates += ["arialbd.ttf"] if bold else []
    candidates += ["ariali.ttf"] if italic else []
    candidates += ["arial.ttf"]
    for name in candidates:
        path = font_dir / name
        if path.exists():
            return ImageFont.truetype(str(path), max(8, int(size * 2.65)))
    return ImageFont.load_default()


def color(value: str | None, default: str = "#000000") -> str | None:
    if not value:
        value = default
    return None if value == "none" else value


class Canvas:
    def __init__(self, width_in: float, height_in: float, scale: int):
        self.width_in = width_in
        self.height_in = height_in
        self.scale = scale
        self.img = Image.new("RGB", (round(width_in * scale), round(height_in * scale)), "white")
        self.draw = ImageDraw.Draw(self.img)

    def pt(self, x: float, y: float) -> tuple[int, int]:
        return round(x * self.scale), round((self.height_in - y) * self.scale)

    def bounds(self, item: dict) -> list[int]:
        x, y, w, h = float(item["x"]), float(item["y"]), float(item["w"]), float(item["h"])
        left, top = self.pt(x, y + h)
        right, bottom = self.pt(x + w, y)
        return [left, top, right, bottom]


def fit_text(c: Canvas, bounds: list[int], item: dict, defaults: dict) -> None:
    text = str(item.get("text", ""))
    if not text:
        return
    family = item.get("font", defaults.get("font", "Times New Roman"))
    size = float(item.get("fontSize", 10))
    bold = bool(item.get("bold", False))
    italic = bool(item.get("italic", False))
    fill = color(item.get("textColor"), "#111111") or "#111111"
    x0, y0, x1, y1 = bounds
    while size > 5:
        f = font(size, bold, italic, family)
        box = c.draw.multiline_textbbox((0, 0), text, font=f, spacing=2, align="center")
        tw, th = box[2] - box[0], box[3] - box[1]
        if tw <= (x1 - x0) * 0.92 and th <= (y1 - y0) * 0.90:
            break
        size -= 0.5
    c.draw.multiline_text((x0 + (x1 - x0 - tw) / 2, y0 + (y1 - y0 - th) / 2), text, font=f, fill=fill, spacing=2, align="center")


def dashed(draw, p1, p2, fill, width=3):
    x0, y0 = p1
    x1, y1 = p2
    length = math.hypot(x1 - x0, y1 - y0)
    if length == 0:
        return
    dx, dy = (x1 - x0) / length, (y1 - y0) / length
    pos = 0
    while pos < length:
        end = min(pos + 12, length)
        draw.line((x0 + dx * pos, y0 + dy * pos, x0 + dx * end, y0 + dy * end), fill=fill, width=width)
        pos += 20


def draw_container(c: Canvas, item: dict, defaults: dict) -> None:
    x0, y0, x1, y1 = c.bounds(item)
    line = color(item.get("line"), "#000000") or "#000000"
    width = max(1, round(float(item.get("lineWeight", 1.25)) * 2))
    radius = round(float(item.get("rounding", 0.16)) * c.scale)
    dashed(c.draw, (x0 + radius, y0), (x1 - radius, y0), line, width)
    dashed(c.draw, (x0 + radius, y1), (x1 - radius, y1), line, width)
    dashed(c.draw, (x0, y0 + radius), (x0, y1 - radius), line, width)
    dashed(c.draw, (x1, y0 + radius), (x1, y1 - radius), line, width)
    c.draw.arc([x0, y0, x0 + 2 * radius, y0 + 2 * radius], 180, 270, fill=line, width=width)
    c.draw.arc([x1 - 2 * radius, y0, x1, y0 + 2 * radius], 270, 360, fill=line, width=width)
    c.draw.arc([x0, y1 - 2 * radius, x0 + 2 * radius, y1], 90, 180, fill=line, width=width)
    c.draw.arc([x1 - 2 * radius, y1 - 2 * radius, x1, y1], 0, 90, fill=line, width=width)
    if item.get("topLabel"):
        fit_text(c, c.bounds({"x": item["x"] + 0.25, "y": item["y"] + item["h"] - 0.42, "w": item["w"] - 0.5, "h": 0.32}), {"text": item["topLabel"], "fontSize": item.get("titleSize", 13), "bold": True}, defaults)
    if item.get("bottomLabel"):
        fit_text(c, c.bounds({"x": item["x"] + 0.25, "y": item["y"] + 0.03, "w": item["w"] - 0.5, "h": 0.30}), {"text": item["bottomLabel"], "fontSize": item.get("labelSize", 13), "bold": True, "italic": True}, defaults)


def draw_connector(c: Canvas, item: dict, defaults: dict) -> None:
    pts = [c.pt(float(p[0]), float(p[1])) for p in item.get("points", [])]
    if len(pts) < 2:
        return
    fill = color(item.get("color"), defaults.get("arrow", "#3F73D1")) or "#3F73D1"
    width = max(1, round(float(item.get("weight", 1.35)) * 2.2))
    for a, b in zip(pts[:-1], pts[1:]):
        dashed(c.draw, a, b, fill, width) if item.get("dashed") else c.draw.line((a, b), fill=fill, width=width)
    if item.get("arrow", "end") != "none":
        x0, y0 = pts[-2]
        x1, y1 = pts[-1]
        angle = math.atan2(y1 - y0, x1 - x0)
        size = 11
        left = (x1 - size * math.cos(angle - math.pi / 6), y1 - size * math.sin(angle - math.pi / 6))
        right = (x1 - size * math.cos(angle + math.pi / 6), y1 - size * math.sin(angle + math.pi / 6))
        c.draw.polygon([(x1, y1), left, right], fill=fill)


def draw_shape(c: Canvas, item: dict, defaults: dict) -> None:
    bounds = c.bounds(item)
    typ = item.get("type", "roundedRect")
    fill = color(item.get("fill"), "#FFFFFF")
    line = color(item.get("line"), defaults.get("line", "#3F73D1"))
    width = max(1, round(float(item.get("lineWeight", 1.1)) * 2))
    if typ == "label":
        fit_text(c, bounds, item, defaults)
        return
    if typ in {"ellipse", "circle"}:
        c.draw.ellipse(bounds, fill=fill, outline=line, width=width)
    elif typ == "diamond":
        x0, y0, x1, y1 = bounds
        pts = [(x0 + x1) / 2, y0], [x1, (y0 + y1) / 2], [(x0 + x1) / 2, y1], [x0, (y0 + y1) / 2]
        c.draw.polygon(pts, fill=fill, outline=line)
        c.draw.line(pts + [pts[0]], fill=line, width=width)
    else:
        radius = 0 if typ == "rect" else round(float(item.get("rounding", 0.06)) * c.scale)
        c.draw.rounded_rectangle(bounds, radius=radius, fill=fill, outline=line, width=width)
    fit_text(c, bounds, item, defaults)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--out")
    parser.add_argument("--scale", type=int, default=160)
    args = parser.parse_args()
    spec_path = Path(args.spec)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    page = spec.get("page", {})
    defaults = spec.get("style", {})
    c = Canvas(float(page.get("width", 15)), float(page.get("height", 8.5)), args.scale)
    for item in spec.get("containers", []):
        draw_container(c, item, defaults)
    for item in spec.get("connectors", []):
        draw_connector(c, item, defaults)
    for item in spec.get("shapes", []):
        draw_shape(c, item, defaults)
    for item in spec.get("labels", []):
        draw_shape(c, {**item, "type": "label"}, defaults)
    out = Path(args.out) if args.out else spec_path.with_suffix(".png")
    c.img.save(out, dpi=(300, 300))
    print(out)


if __name__ == "__main__":
    main()
