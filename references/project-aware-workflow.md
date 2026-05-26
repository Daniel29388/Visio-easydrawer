# Project-Aware Figure Workflow

Use this when the user asks to draw a model architecture from a paper/project directory rather than only from a reference image.

## What Can Be Automated

- Ultralytics/YOLO/RT-DETR-like YAML configs: generate a first-pass architecture spec with `scripts/yaml_to_figure_spec.py`.
- LaTeX papers: extract included figure paths, captions, document class hints, and existing figure naming patterns with `scripts/scan_paper_project.py`.
- Existing PNG/SVG/PDF figures: use them as visual references for layout and legend style.
- Python modules: scan class/function names to identify likely custom blocks, then let Codex inspect the relevant files and construct the spec.

## Important Boundary

Do not claim that arbitrary Python models can be perfectly parsed automatically. For custom segmentation networks, graph neural networks, diffusion modules, or heavily dynamic `forward()` code:

1. Scan the project for likely files.
2. Read the model class and relevant blocks.
3. Infer the architecture manually as Codex.
4. Write a figure spec and run preview/audit scripts.

The automation provides discovery, drafting, styling, and rendering. Codex still owns the architecture interpretation when the project is not configuration-driven.

## Recommended Procedure

1. Run project scan:

```powershell
python "C:\Users\Administrator\.codex\skills\visio-figure-redrawer\scripts\scan_paper_project.py" --project "path\to\project" --out "path\to\project.figure-context.json" --markdown "path\to\project.figure-context.md"
```

2. If a model YAML exists, draft a spec:

```powershell
python "C:\Users\Administrator\.codex\skills\visio-figure-redrawer\scripts\yaml_to_figure_spec.py" --yaml "path\to\model.yaml" --out "path\to\model.figure.json" --title "Model Architecture"
```

3. If only Python code exists:
   - Read the model entry file, custom blocks, and any config files.
   - Use `references/figure-spec-schema.md` to write `model.figure.json`.
   - Preserve user-provided naming and any paper notation.

4. Apply reference/journal style:
   - If there is a reference image, mimic it first.
   - If a target journal is named, apply the closest profile and tune manually.

5. Audit, preview, render:

```powershell
python "C:\Users\Administrator\.codex\skills\visio-figure-redrawer\scripts\audit_figure_spec.py" --spec "path\to\model.figure.json" --out "path\to\model.audit.md"
python "C:\Users\Administrator\.codex\skills\visio-figure-redrawer\scripts\render_preview_from_spec.py" --spec "path\to\model.figure.json" --out "path\to\model.preview.png"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\Administrator\.codex\skills\visio-figure-redrawer\scripts\draw_visio_from_spec.ps1" -SpecPath "path\to\model.figure.json" -OutVsdx "path\to\model.vsdx"
```

## Segmentation / Detection / Classification Hints

- Detection: show backbone, neck/FPN/PAN/encoder, query/head/decoder, and P3/P4/P5 outputs if present.
- Segmentation: show encoder, bottleneck/context module, decoder/upsampling path, skip connections, mask head, and auxiliary heads.
- Classification: show stem, stages, attention/context blocks, pooling, classifier head.
- Multimodal models: show each modality branch, fusion point, shared encoder, task heads.
