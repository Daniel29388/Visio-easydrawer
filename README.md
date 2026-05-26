# Visio Figure Redrawer

Codex skill for turning reference figures and paper/model projects into editable Microsoft Visio `.vsdx` diagrams.

## What Makes This Different

This skill is not only an image-to-Visio redraw helper. It is project-aware:

- Reference-first redraw: mimic an arbitrary reference figure's legend, layout, colors, arrows, and grouping.
- Project-aware drafting: scan paper/model folders for YAML configs, Python model files, LaTeX figure references, captions, and existing figures.
- YAML-to-figure drafting: create a first-pass architecture diagram from YOLO/RT-DETR/Ultralytics-like model YAML files.
- Journal-aware styling: apply Nature-like, IEEE-like, Elsevier-like, IOP/SPIE-like, or reference-first style profiles.
- QA loop: audit JSON specs, render preview PNGs, then generate editable Visio.

Compared with scene-centric Visio reconstruction tools such as [Rss3208/Visiomaster](https://github.com/Rss3208/Visiomaster), this skill is lighter and more Codex-native. It borrows useful release and QA ideas, such as an intermediate JSON spec, audit before rendering, environment checks, and examples, but focuses on letting Codex read a paper project and design the figure structure before rendering.

## Install

Clone or copy this folder into your Codex skills directory:

```powershell
git clone https://github.com/<owner>/visio-figure-redrawer.git "$env:USERPROFILE\.codex\skills\visio-figure-redrawer"
cd "$env:USERPROFILE\.codex\skills\visio-figure-redrawer"
python -m pip install -r requirements.txt
```

Then invoke it in Codex:

```text
Use $visio-figure-redrawer to read this project and draw a journal-ready Visio architecture figure.
```

## Requirements

- Windows for `.vsdx` rendering.
- Desktop Microsoft Visio.
- Python 3.10+.
- Python packages in `requirements.txt`.

Check the local environment:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\check_environment.ps1
```

## Typical Workflows

### Redraw A Reference Figure

1. Codex inspects the reference image.
2. Codex writes a JSON figure spec using `references/figure-spec-schema.md`.
3. Render preview and Visio:

```powershell
python .\scripts\render_preview_from_spec.py --spec .\work\figure.json --out .\work\figure-preview.png
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\draw_visio_from_spec.ps1 -SpecPath .\work\figure.json -OutVsdx .\work\figure.vsdx
```

### Read A Paper Or Model Project

```powershell
python .\scripts\scan_paper_project.py --project C:\path\project --out .\work\project.figure-context.json --markdown .\work\project.figure-context.md
```

If the project has a model YAML:

```powershell
python .\scripts\yaml_to_figure_spec.py --yaml C:\path\model.yaml --out .\work\model.figure.json --title "Model Architecture"
```

Then apply a journal style if needed:

```powershell
python .\scripts\apply_journal_profile.py --spec .\work\model.figure.json --profile ieee-grayscale --out .\work\model.ieee.json --force
```

Audit, preview, render:

```powershell
python .\scripts\audit_figure_spec.py --spec .\work\model.ieee.json --out .\work\model.audit.md
python .\scripts\render_preview_from_spec.py --spec .\work\model.ieee.json --out .\work\model.preview.png
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\draw_visio_from_spec.ps1 -SpecPath .\work\model.ieee.json -OutVsdx .\work\model.vsdx
```

## Built-In Style Profiles

Profiles live in `assets/journal-style-profiles.json`:

- `reference-first`
- `nature-minimal`
- `ieee-grayscale`
- `elsevier-clean`
- `iop-spie-technical`

These profiles are starting points. For final submission, verify the target journal's current artwork instructions.

## Core Files

- `SKILL.md`: skill trigger and workflow.
- `scripts/scan_paper_project.py`: scan project folders for figure context.
- `scripts/yaml_to_figure_spec.py`: draft model architecture figures from YAML.
- `scripts/audit_figure_spec.py`: detect spec risks before rendering.
- `scripts/draw_visio_from_spec.ps1`: generate editable Visio from JSON.
- `scripts/render_preview_from_spec.py`: render PNG preview from JSON.
- `scripts/apply_journal_profile.py`: apply journal/style profiles.
- `references/project-aware-workflow.md`: project-to-figure workflow.
- `references/reference-first-workflow.md`: reference image extraction checklist.
- `references/figure-spec-schema.md`: JSON figure spec schema.
- `references/release-checklist.md`: GitHub release checklist.

## Limitations

- Arbitrary Python `forward()` graphs still require Codex interpretation.
- The YAML drafter targets YOLO/RT-DETR/Ultralytics-like sequential configs and produces a first pass, not a final polished paper figure.
- `.vsdx` rendering requires Windows and desktop Microsoft Visio.
- Journal profiles are not a substitute for checking the latest author guidelines.
