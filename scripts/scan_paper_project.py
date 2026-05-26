#!/usr/bin/env python
"""Scan a paper/model project for figure-building context."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".pdf", ".eps", ".tif", ".tiff"}
TEXT_EXTS = {".tex", ".md", ".txt", ".rst"}
YAML_EXTS = {".yaml", ".yml"}
CODE_EXTS = {".py"}


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


def read_text(path: Path, limit: int = 250_000) -> str:
    data = path.read_bytes()[:limit]
    for enc in ("utf-8", "utf-8-sig", "gbk", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def scan_tex(path: Path) -> dict:
    text = read_text(path)
    figures = re.findall(r"\\(?:includegraphics|safeincludegraphics)(?:\[[^\]]*\])?\{([^}]+)\}", text)
    captions = re.findall(r"\\caption(?:\[[^\]]*\])?\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", text)
    cls = re.findall(r"\\documentclass(?:\[[^\]]*\])?\{([^}]+)\}", text)
    return {"figures": figures[:50], "captions": captions[:20], "documentclass": cls[:3]}


def scan_yaml(path: Path) -> dict:
    text = read_text(path)
    modules = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- ["):
            continue
        comment = ""
        if "#" in stripped:
            stripped, comment = stripped.split("#", 1)
            comment = comment.strip()
        m = re.search(r",\s*([A-Za-z_][A-Za-z0-9_\.]*)\s*,\s*\[", stripped)
        if m:
            modules.append({"module": m.group(1), "comment": comment})
    return {"modules": modules[:120], "module_count": len(modules)}


def scan_code(path: Path) -> dict:
    text = read_text(path, 160_000)
    classes = re.findall(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)", text, flags=re.M)
    funcs = re.findall(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)", text, flags=re.M)
    return {"classes": classes[:80], "functions": funcs[:80]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=".", help="Project root")
    parser.add_argument("--out", help="Write JSON summary")
    parser.add_argument("--markdown", help="Write Markdown summary")
    parser.add_argument("--max-files", type=int, default=500)
    args = parser.parse_args()

    root = Path(args.project).resolve()
    files = [p for p in root.rglob("*") if p.is_file()]
    files = [p for p in files if ".git" not in p.parts and "__pycache__" not in p.parts]
    files = files[: args.max_files]

    summary = {
        "root": str(root),
        "yaml": [],
        "tex": [],
        "images": [],
        "code": [],
        "candidate_reference_images": [],
        "candidate_model_configs": [],
        "candidate_journal": [],
    }

    for p in files:
        ext = p.suffix.lower()
        entry = {"path": rel(p, root), "bytes": p.stat().st_size}
        if ext in YAML_EXTS:
            entry.update(scan_yaml(p))
            summary["yaml"].append(entry)
            if entry.get("module_count", 0) > 3:
                summary["candidate_model_configs"].append(entry["path"])
        elif ext in TEXT_EXTS:
            if ext == ".tex":
                entry.update(scan_tex(p))
                if entry.get("documentclass"):
                    summary["candidate_journal"].extend(entry["documentclass"])
            summary["tex"].append(entry)
        elif ext in IMAGE_EXTS:
            summary["images"].append(entry)
            name = p.name.lower()
            if any(k in name for k in ("overall", "architecture", "framework", "module", "fig", "figure", "网络", "结构")):
                summary["candidate_reference_images"].append(entry["path"])
        elif ext in CODE_EXTS:
            entry.update(scan_code(p))
            if entry.get("classes") or entry.get("functions"):
                summary["code"].append(entry)

    if args.out:
        Path(args.out).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.markdown:
        lines = [
            "# Paper Project Figure Context",
            "",
            f"Root: `{summary['root']}`",
            "",
            "## Candidate Model Configs",
            *[f"- `{p}`" for p in summary["candidate_model_configs"][:20]],
            "",
            "## Candidate Reference Images",
            *[f"- `{p}`" for p in summary["candidate_reference_images"][:30]],
            "",
            "## TeX Figure References",
        ]
        for tex in summary["tex"][:15]:
            if tex.get("figures"):
                lines.append(f"- `{tex['path']}`: " + ", ".join(f"`{f}`" for f in tex["figures"][:8]))
        lines += ["", "## Detected Document Classes", *[f"- `{c}`" for c in sorted(set(summary["candidate_journal"]))]]
        Path(args.markdown).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "yaml": len(summary["yaml"]),
        "tex": len(summary["tex"]),
        "images": len(summary["images"]),
        "code": len(summary["code"]),
        "candidate_model_configs": summary["candidate_model_configs"][:5],
        "candidate_reference_images": summary["candidate_reference_images"][:5],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
