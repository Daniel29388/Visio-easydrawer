---
name: visio-figure-redrawer
description: Redraw arbitrary reference figures, screenshots, paper diagrams, model architectures, module diagrams, flowcharts, and paper/project neural-network structures as editable Microsoft Visio `.vsdx` files with preview PNGs. Use when Codex is asked to mimic a figure, convert an image to Visio, read a paper/project/YAML/codebase and design an architecture figure, create a journal-ready model diagram for detection, segmentation, classification, YOLO, RT-DETR, transformer, multimodal, or custom neural networks, or adapt a diagram style for Nature, IEEE, Elsevier, IOP, SPIE, or other submission targets while preserving the reference figure first.
---

# Visio Figure Redrawer

## Decision Order

1. Reference figure first.
   - Preserve the supplied figure's structure, labels, layout grammar, stage grouping, colors, and arrows.
   - Treat the reference as the primary legend unless the user provides a separate legend, code, YAML, or paper text.

2. Project evidence second.
   - If the user provides a project or paper folder, scan it for model YAML, Python modules, LaTeX figure references, captions, and existing figure assets.
   - For YOLO/RT-DETR-like YAML, generate a first-pass spec automatically.
   - For arbitrary Python models, inspect the relevant code and infer the architecture as Codex; do not pretend dynamic `forward()` graphs are always fully parseable.

3. Journal style third.
   - If the user names a target journal, adapt typography, line weight, page ratio, color saturation, and grayscale safety.
   - Verify current journal artwork instructions when final compliance matters.
   - If journal style conflicts with the reference, preserve reference semantics and make minimal publication-style adjustments.

4. Drawing polish last.
   - Improve alignment, spacing, text fitting, arrow routing, and visual hierarchy without changing meaning.

## Workflow

1. Inspect source material.
   - Use image viewing for reference images.
   - For project folders, run `scripts/scan_paper_project.py` and read `references/project-aware-workflow.md`.
   - For reference-only redraws, read `references/reference-first-workflow.md`.

2. Create or draft a generic figure spec.
   - Use `references/figure-spec-schema.md`.
   - Coordinates are inches from the lower-left corner.
   - Use editable `containers`, `shapes`, `labels`, and `connectors`; do not paste the source image into Visio as the final content.
   - Assign `kind` values such as `conv`, `sampling`, `fusion`, `interaction`, `feature`, `query`, `decoder`, `output`, or `default`.

3. For model YAML, draft automatically:

```powershell
python "C:\Users\Administrator\.codex\skills\visio-figure-redrawer\scripts\yaml_to_figure_spec.py" --yaml "path\to\model.yaml" --out "path\to\model.figure.json" --title "Model Architecture"
```

4. Optionally apply a journal profile:

```powershell
python "C:\Users\Administrator\.codex\skills\visio-figure-redrawer\scripts\apply_journal_profile.py" --spec "path\to\figure.json" --profile "nature-minimal" --out "path\to\figure.nature.json" --force
```

Profiles live in `assets/journal-style-profiles.json`: `reference-first`, `nature-minimal`, `ieee-grayscale`, `elsevier-clean`, and `iop-spie-technical`.

5. Audit and preview:

```powershell
python "C:\Users\Administrator\.codex\skills\visio-figure-redrawer\scripts\audit_figure_spec.py" --spec "path\to\figure.json" --out "path\to\figure.audit.md"
python "C:\Users\Administrator\.codex\skills\visio-figure-redrawer\scripts\render_preview_from_spec.py" --spec "path\to\figure.json" --out "path\to\figure-preview.png"
```

6. Generate editable Visio:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\Administrator\.codex\skills\visio-figure-redrawer\scripts\draw_visio_from_spec.ps1" -SpecPath "path\to\figure.json" -OutVsdx "path\to\figure.vsdx"
```

7. Visually QA and iterate.
   - Open/view the preview PNG.
   - Check text overflow, arrowhead clarity, frame-label spacing, ambiguous skip connections, and journal readability.
   - Regenerate preview and `.vsdx` after spec edits.

## Practical Defaults

- Start from `assets/generic-architecture-example.json` when no better structure exists.
- Use `reference-first` when the user asks to mimic a supplied figure and does not name a journal.
- Use `ieee-grayscale` when the figure may appear in a compact two-column or grayscale setting.
- Use `nature-minimal` for clean high-impact-journal drafts, but verify current journal guidance before final submission.
- Deliver `.vsdx`, preview PNG, and the JSON spec whenever possible.
- If Visio PNG export hangs, ignore it and use the Python preview renderer.
