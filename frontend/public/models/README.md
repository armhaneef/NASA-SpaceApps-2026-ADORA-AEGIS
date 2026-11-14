# Digital-twin model asset

The viewer looks for the team-provided anatomical model at:

```text
frontend/public/models/astronaut-anatomy.glb
```

Place the approved GLB at that path. The file is intentionally not included;
the application uses an explicitly labeled, non-anatomical holographic
contour when the asset is absent, and reports a useful status if loading fails.
No external model is downloaded.

## Region mesh names

The viewer normalizes the model's vertical bounds and centers it automatically.
For region-specific mesh highlighting, name mesh nodes (or set a `region`
property in node `userData`) so their names contain one of these terms:

| Region | Recognized mesh-name terms |
|---|---|
| Head | `head`, `brain`, `cranial`, `skull` |
| Heart | `heart`, `cardiac` |
| Lungs | `lung`, `pulmonary` |
| Abdomen | `abdomen`, `abdominal`, `stomach`, `core` |

Use separate named meshes for individual organs when possible. The four viewer
hotspots remain interactive even if a mesh is not named; naming enables the
viewer to highlight the corresponding GLB mesh. A GLB should use a vertical
Y-up human pose and face +Z for the initial front view.

The model must be supplied and reviewed by the Digital Twin team. The viewer's
hotspots and synthetic telemetry do not establish anatomical accuracy or
clinical validity.
