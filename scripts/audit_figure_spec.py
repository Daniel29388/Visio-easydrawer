#!/usr/bin/env python
"""Audit a generic figure spec before Visio rendering."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def overlap(a: dict, b: dict) -> float:
    ax0, ay0, ax1, ay1 = a["x"], a["y"], a["x"] + a["w"], a["y"] + a["h"]
    bx0, by0, bx1, by1 = b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]
    ix = max(0, min(ax1, bx1) - max(ax0, bx0))
    iy = max(0, min(ay1, by1) - max(ay0, by0))
    return ix * iy


def text_risk(item: dict) -> bool:
    text = str(item.get("text", ""))
    if not text:
        return False
    lines = text.splitlines() or [text]
    longest = max((len(x) for x in lines), default=0)
    width = float(item.get("w", 1))
    height = float(item.get("h", 0.4))
    # Conservative preflight only: the preview renderer dynamically shrinks text.
    return longest > max(12, int(width * 16)) or len(lines) > max(3, int(height * 8))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--out")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    page = spec.get("page", {"width": 15, "height": 8.5})
    shapes = spec.get("shapes", []) + [{**x, "type": "label"} for x in spec.get("labels", [])]
    connectors = spec.get("connectors", [])
    issues = []

    for item in shapes:
        x, y, w, h = map(float, (item.get("x", 0), item.get("y", 0), item.get("w", 0), item.get("h", 0)))
        if x < 0 or y < 0 or x + w > page.get("width", 15) or y + h > page.get("height", 8.5):
            issues.append(("bounds", item.get("id", "?"), "Shape exceeds page bounds."))
        if text_risk(item):
            issues.append(("text-fit", item.get("id", "?"), "Text may not fit the shape."))

    for i, a in enumerate(shapes):
        if a.get("type") == "label":
            continue
        for b in shapes[i + 1:]:
            if b.get("type") == "label":
                continue
            area = overlap(a, b)
            if area > 0.02:
                issues.append(("overlap", f"{a.get('id', '?')} / {b.get('id', '?')}", f"Shapes overlap by about {area:.2f} square inches."))

    for i, conn in enumerate(connectors):
        pts = conn.get("points", [])
        if len(pts) < 2:
            issues.append(("connector", f"connector-{i}", "Connector has fewer than two points."))
        for p in pts:
            if len(p) != 2:
                issues.append(("connector", f"connector-{i}", "Connector point is not [x, y]."))

    by_kind = {}
    for item in shapes:
        kind = item.get("kind", item.get("type", "default"))
        by_kind[kind] = by_kind.get(kind, 0) + 1

    lines = [
        "# Figure Spec Audit",
        "",
        f"Spec: `{spec_path}`",
        f"Page: `{page.get('width', 15)} x {page.get('height', 8.5)} in`",
        f"Shapes: `{len(shapes)}`",
        f"Connectors: `{len(connectors)}`",
        "",
        "## Shape Kinds",
    ]
    for kind, count in sorted(by_kind.items()):
        lines.append(f"- `{kind}`: {count}")
    lines += ["", "## Issues"]
    if issues:
        for severity, target, message in issues:
            lines.append(f"- `{severity}` `{target}`: {message}")
    else:
        lines.append("- None detected.")

    output = "\n".join(lines) + "\n"
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
