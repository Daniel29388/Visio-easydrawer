#!/usr/bin/env python
"""Apply a journal/style profile to a generic figure spec."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def infer_kind(item: dict) -> str:
    if item.get("kind"):
        return str(item["kind"])
    text = f"{item.get('id', '')} {item.get('text', '')}".lower()
    rules = [
        ("sampling", ("pool", "unpool", "sample", "upsample", "downsample", "resize", "wavelet")),
        ("fusion", ("concat", "fusion", "merge", "add", "sum", "cat")),
        ("interaction", ("attention", "transformer", "encoder", "decoder layer", "repc3", "mlp", "ffn")),
        ("conv", ("conv", "projection", "proj", "dwconv", "bn")),
        ("query", ("query", "selection")),
        ("decoder", ("decoder", "head")),
        ("output", ("output", "class", "box", "mask", "prediction")),
        ("feature", ("p3", "p4", "p5", "f3", "f4", "f5", "y3", "y4", "y5")),
        ("backbone", ("backbone", "c2f", "stage", "block")),
    ]
    for kind, keys in rules:
        if any(k in text for k in keys):
            return kind
    return "default"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--profiles")
    parser.add_argument("--out")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--preserve-page", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    profiles_path = Path(args.profiles) if args.profiles else root / "assets" / "journal-style-profiles.json"
    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
    if args.profile not in profiles:
        raise SystemExit(f"Unknown profile '{args.profile}'. Available: {', '.join(sorted(profiles))}")

    profile = profiles[args.profile]
    spec_path = Path(args.spec)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spec.setdefault("style", {})
    if profile.get("page") and not args.preserve_page:
        spec["page"] = profile["page"]
    spec.setdefault("page", profile.get("page", {"width": 15.0, "height": 8.5}))

    for key in ("font", "line", "arrow"):
        if args.force or key not in spec["style"]:
            spec["style"][key] = profile[key]

    fills = profile.get("fills", {})
    for item in spec.get("shapes", []):
        kind = infer_kind(item)
        item.setdefault("kind", kind)
        if kind in fills and (args.force or "fill" not in item):
            item["fill"] = fills[kind]
        if args.force or "line" not in item:
            item["line"] = profile["line"]
        if args.force or "font" not in item:
            item["font"] = profile["font"]
    for item in spec.get("labels", []):
        if args.force or "font" not in item:
            item["font"] = profile["font"]
    for item in spec.get("connectors", []):
        if args.force or "color" not in item:
            item["color"] = profile["arrow"]

    spec.setdefault("metadata", {})
    spec["metadata"]["journalProfile"] = args.profile
    spec["metadata"]["journalProfileNote"] = profile.get("note", "")
    out = Path(args.out) if args.out else spec_path.with_name(f"{spec_path.stem}.{args.profile}.json")
    out.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
