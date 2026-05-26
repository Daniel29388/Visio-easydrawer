# Reference-First Redrawing Workflow

Use this when the user provides any reference figure or screenshot and asks for a Visio redraw.

## Priority Order

1. Reference figure first.
   - Preserve the user's visible structure, labels, hierarchy, arrows, and visual grammar.
   - Extract the legend implicitly: colors, repeated shapes, line styles, and stage frames.
   - Do not invent missing modules unless the user supplies code/YAML/paper text to justify them.

2. Target journal second.
   - If a target journal is named, adapt font, line weight, color saturation, page ratio, and grayscale safety.
   - If the reference conflicts with the journal style, keep structure and semantics from the reference while making only publication-style adjustments.
   - For final submission requirements that may change, verify the current journal artwork guide before claiming compliance.

3. Codex design judgment third.
   - Improve spacing, alignment, text fit, arrow routing, and readability.
   - Keep edits faithful and reversible: final output should be editable Visio shapes.

## Extraction Checklist

- Page orientation and aspect ratio.
- Stage groups and frame labels.
- Repeated node families and their colors.
- Arrow directions, branch/merge points, skip connections, dashed links.
- Text hierarchy: title, stage labels, module labels, scale labels, captions.
- Special notation: P3/P4/P5, xN repeats, tensor sizes, mathematical symbols.
- Output artifacts requested: `.vsdx`, preview PNG, SVG/PDF export if needed.

## Drawing Checklist

- Draw containers first, connectors second, nodes and labels last.
- Use short module labels; line-break long labels with `\n`.
- Route arrows orthogonally for architecture diagrams.
- Keep arrowheads clear of frames and node borders.
- Preview before delivery and iterate on overlap or cramped text.
