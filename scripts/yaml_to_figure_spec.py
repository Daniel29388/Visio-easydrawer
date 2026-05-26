#!/usr/bin/env python
"""Create a first-pass editable architecture figure spec from a model YAML."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


FILL = {
    "conv": "#DCEEFF",
    "backbone": "#FFF0C7",
    "sampling": "#DDEFD6",
    "fusion": "#FFC8C8",
    "interaction": "#B9B2FF",
    "feature": "#F8D9C8",
    "query": "#FFF1C7",
    "decoder": "#BBD7F0",
    "output": "#DCEEFF",
    "default": "#FFFFFF",
}


def kind_for(module: str) -> str:
    key = module.lower()
    if any(k in key for k in ("concat", "add", "sum", "fusion")):
        return "fusion"
    if any(k in key for k in ("pool", "unpool", "sample", "resize", "wavelet")):
        return "sampling"
    if any(k in key for k in ("attention", "transformer", "encoder", "aifi", "nacpg", "repc3", "c3")):
        return "interaction"
    if "decoder" in key or "detect" in key:
        return "decoder"
    if any(k in key for k in ("conv", "bn", "dw")):
        return "conv"
    if any(k in key for k in ("c2f", "block", "bottleneck")):
        return "backbone"
    return "default"


def short_label(module: str, repeats: int | str | None = None) -> str:
    label = str(module).split(".")[-1]
    replacements = {
        "TransformerEncoderLayer_NACPG": "NACPG",
        "TransformerEncoderLayer": "Transformer\nEncoder",
        "RTDETRDecoder": "RT-DETR\nDecoder",
        "LWaveletUnPool": "LWavelet\nUnPool",
        "LWaveletPool": "LWavelet\nPool",
        "C2f_IEL_BDCG": "C2f_IEL_BDCG",
    }
    label = replacements.get(label, label)
    if repeats and str(repeats) not in {"1", "-1"}:
        label += f" x{repeats}"
    return label


def parse_yaml(path: Path) -> tuple[list[dict], list[dict]]:
    if yaml is not None:
        data = yaml.safe_load(path.read_text(encoding="utf-8", errors="ignore"))
        return read_section(data.get("backbone", [])), read_section(data.get("head", []))
    return parse_by_regex(path.read_text(encoding="utf-8", errors="ignore"))


def read_section(section: list) -> list[dict]:
    out = []
    for i, row in enumerate(section):
        if not isinstance(row, list) or len(row) < 3:
            continue
        from_, repeats, module = row[0], row[1], str(row[2])
        out.append({"index": i, "from": from_, "repeats": repeats, "module": module, "comment": ""})
    return out


def parse_by_regex(text: str) -> tuple[list[dict], list[dict]]:
    current = None
    sections = {"backbone": [], "head": []}
    for line in text.splitlines():
        if re.match(r"^\s*backbone\s*:", line):
            current = "backbone"
            continue
        if re.match(r"^\s*head\s*:", line):
            current = "head"
            continue
        if current and line.strip().startswith("- ["):
            raw = line.strip()
            comment = ""
            if "#" in raw:
                raw, comment = raw.split("#", 1)
                comment = comment.strip()
            m = re.search(r"\[\s*([^,\]]+).*?,\s*([^,\]]+)\s*,\s*([A-Za-z_][A-Za-z0-9_\.]*)", raw)
            if m:
                sections[current].append({
                    "index": len(sections[current]),
                    "from": m.group(1),
                    "repeats": m.group(2),
                    "module": m.group(3),
                    "comment": comment,
                })
    return sections["backbone"], sections["head"]


def y_positions(count: int, top: float, bottom: float) -> list[float]:
    if count <= 1:
        return [(top + bottom) / 2]
    step = (top - bottom) / (count - 1)
    return [top - i * step for i in range(count)]


def make_spec(backbone: list[dict], head: list[dict], title: str) -> dict:
    width, height = 15.0, 8.5
    shapes = []
    connectors = []
    containers = [
        {"id": "backbone-frame", "x": 0.35, "y": 0.45, "w": 2.25, "h": 7.65, "bottomLabel": "Backbone"},
        {"id": "body-frame", "x": 2.95, "y": 0.45, "w": 8.75, "h": 7.65, "topLabel": title, "bottomLabel": "Neck / Encoder"},
        {"id": "head-frame", "x": 12.05, "y": 0.45, "w": 2.45, "h": 7.65, "bottomLabel": "Head"},
    ]

    by_index = {}
    by_global = {}
    bx, bw, bh = 0.70, 1.55, 0.36
    for row, y in zip(backbone, y_positions(max(len(backbone), 1), 7.15, 1.28)):
        kind = kind_for(row["module"])
        sid = f"b{row['index']}"
        shapes.append({"id": sid, "kind": kind, "x": bx, "y": y, "w": bw, "h": bh, "text": short_label(row["module"], row["repeats"]), "fill": FILL[kind], "fontSize": 7.8})
        by_global[row["index"]] = (bx + bw, y + bh / 2)
        by_index[sid] = (bx, y, bw, bh)
    for i in range(len(backbone) - 1):
        y1 = by_index[f"b{i}"][1]
        y2 = by_index[f"b{i+1}"][1]
        connectors.append({"points": [[bx + bw / 2, y1], [bx + bw / 2, y2 + bh]], "weight": 1.15})

    body_head = []
    final_decoder = None
    for row in head:
        if kind_for(row["module"]) == "decoder":
            final_decoder = row
        else:
            body_head.append(row)

    head_count = len(body_head)
    rows = min(max(head_count, 1), 12)
    columns = 4
    x0, y_top, dx, dy = 3.30, 6.65, 2.00, 1.05
    head_points = {}
    for i, row in enumerate(body_head):
        col = i % columns
        line = i // columns
        x = x0 + col * dx
        y = y_top - line * dy
        if y < 1.30:
            y = 1.30
        kind = kind_for(row["module"])
        sid = f"h{i}"
        shapes.append({"id": sid, "kind": kind, "x": x, "y": y, "w": 1.18, "h": 0.40, "text": short_label(row["module"], row["repeats"]), "fill": FILL[kind], "fontSize": 7.6})
        head_points[i] = (x, y, 1.18, 0.40)
        if i > 0:
            prev = head_points[i - 1]
            connectors.append({"points": [[prev[0] + prev[2], prev[1] + prev[3] / 2], [x, y + 0.20]], "weight": 1.1})

    # Connect likely backbone outputs to the body.
    for j, idx in enumerate(sorted(by_global)[-3:]):
        y = [6.85, 4.60, 2.35][j]
        sx, sy = by_global[idx]
        connectors.append({"points": [[sx, sy], [2.85, sy], [2.85, y], [3.30, y]], "weight": 1.1})
        shapes.append({"id": f"scale{j}", "type": "label", "x": 2.62, "y": y - 0.10, "w": 0.28, "h": 0.24, "text": f"P{5-j}", "fontSize": 9, "bold": True, "italic": True})

    decoder_text = "Decoder\nHead"
    if final_decoder:
        decoder_text = short_label(final_decoder["module"], None)
    shapes.extend([
        {"id": "query", "kind": "query", "x": 12.38, "y": 1.55, "w": 0.86, "h": 5.55, "text": "Query\nSelection", "fill": FILL["query"], "line": FILL["query"], "fontSize": 10.5},
        {"id": "decoder", "kind": "decoder", "x": 13.42, "y": 1.55, "w": 0.86, "h": 5.55, "text": decoder_text, "fill": FILL["decoder"], "line": FILL["decoder"], "fontSize": 10.5},
    ])
    connectors.append({"points": [[11.70, 4.35], [12.38, 4.35]], "weight": 1.2})
    connectors.append({"points": [[13.24, 4.35], [13.42, 4.35]], "weight": 1.2})

    return {
        "metadata": {"source": "yaml_to_figure_spec.py", "title": title},
        "page": {"width": width, "height": height},
        "style": {"font": "Times New Roman", "line": "#3F73D1", "arrow": "#3F73D1"},
        "containers": containers,
        "connectors": connectors,
        "shapes": shapes,
        "labels": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--yaml", required=True, help="Model YAML path")
    parser.add_argument("--out", required=True, help="Output figure spec JSON")
    parser.add_argument("--title", default="", help="Diagram title")
    args = parser.parse_args()
    path = Path(args.yaml)
    backbone, head = parse_yaml(path)
    title = args.title or path.stem.replace("_", " ").replace("-", " ")
    spec = make_spec(backbone, head, title)
    Path(args.out).write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"backbone": len(backbone), "head": len(head), "out": args.out}, indent=2))


if __name__ == "__main__":
    main()
