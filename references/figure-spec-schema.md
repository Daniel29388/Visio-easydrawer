# Generic Figure Spec Schema

The scripts consume one JSON file. Coordinates are inches from the lower-left page corner.

## Minimal Structure

```json
{
  "page": { "width": 15.0, "height": 8.5 },
  "style": { "font": "Times New Roman", "line": "#3F73D1", "arrow": "#3F73D1" },
  "containers": [],
  "connectors": [],
  "shapes": [],
  "labels": []
}
```

## Containers

Dashed rounded stage frames.

```json
{ "id": "backbone", "x": 0.4, "y": 0.5, "w": 2.0, "h": 7.4, "topLabel": "Backbone" }
```

Optional fields: `bottomLabel`, `titleSize`, `labelSize`, `rounding`, `line`, `lineWeight`.

## Shapes

Editable Visio nodes.

```json
{
  "id": "conv1",
  "type": "roundedRect",
  "kind": "conv",
  "x": 3.0,
  "y": 5.2,
  "w": 1.2,
  "h": 0.45,
  "text": "Conv",
  "fill": "#DCEEFF"
}
```

Supported `type`: `roundedRect`, `rect`, `ellipse`, `circle`, `label`. The preview renderer also supports `diamond`; the Visio renderer approximates unsupported types as editable rectangles if needed.

Recommended `kind` values for journal profiles: `conv`, `backbone`, `sampling`, `fusion`, `interaction`, `feature`, `query`, `decoder`, `output`, `default`.

## Connectors

Orthogonal or straight line segments. The final segment receives an arrowhead unless `arrow` is `none`.

```json
{ "points": [[4.2, 5.4], [5.2, 5.4], [5.2, 4.1]], "weight": 1.35 }
```

Optional fields: `color`, `dashed`, `arrow`, `weight`.

## Labels

Frameless text blocks. Equivalent to `shapes` with `type: "label"`.

```json
{ "x": 1.0, "y": 7.7, "w": 1.0, "h": 0.3, "text": "Input", "bold": true, "italic": true }
```
