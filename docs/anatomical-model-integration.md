# Anatomical model integration

## Asset and license

The viewer loads the existing local asset at
[`../frontend/public/models/adora-anatomy.glb`](../frontend/public/models/adora-anatomy.glb).
It is the `anatomy-male.glb` model from
[open-anatomy-3d 0.1.0](https://github.com/MervinR07/open-anatomy-3d), copied
locally as `adora-anatomy.glb`. The project and versioned package documents
were checked:

- [Original model file](https://cdn.jsdelivr.net/npm/open-anatomy-3d@0.1.0/models/anatomy-male.glb).
- [Model license](https://cdn.jsdelivr.net/npm/open-anatomy-3d@0.1.0/LICENSE-MODELS.md):
  Creative Commons Attribution 4.0 International (CC BY 4.0).
- [Required attribution and upstream sources](https://cdn.jsdelivr.net/npm/open-anatomy-3d@0.1.0/ATTRIBUTION.md).
- [CC BY 4.0 license text](https://creativecommons.org/licenses/by/4.0/).

The versioned upstream attribution file specifies this credit line:

> Anatomy: BodyParts3D © The Database Center for Life Science (CC BY 4.0);
> female organs: Human Reference Atlas 3D Reference Organs, HuBMAP (CC BY 4.0);
> female body: MakeHuman (CC0). Modified by open-anatomy-3d
> (https://github.com/MervinR07/open-anatomy-3d), CC BY 4.0.

This project uses the male model; the HuBMAP and MakeHuman entries in the
upstream package's standard credit line refer to female-model components not
present in this asset. The viewer adds AEGIS holographic materials and
runtime centering/scaling; the GLB itself is not altered. The 3D model license
is separate from the upstream source-code MIT license.

The source project describes the model as an educational visualization, not
for diagnosis or clinical decisions. It is not a NASA asset or endorsement.

## GLB inspection

The local file was inspected without downloading or replacing it:

| Property | Verified result |
|---|---|
| File size | 7,614,076 bytes |
| Header / version | `glTF`, version 2 |
| Declared length | 7,614,076 bytes; matches the file size |
| Generator | glTF-Transform v4.5.0 |
| Scene | `anatomy` |
| Nodes / meshes | 134 nodes / 128 meshes |
| Explicit materials | None; the viewer assigns its own cloned holographic materials |
| Required extensions | `EXT_meshopt_compression`, `KHR_mesh_quantization` |
| Meshopt | Present and required; decoded by Three.js `MeshoptDecoder` |
| Geometry | Approximately 1,026,032 triangles, estimated from indexed triangle primitives |
| Coordinates | Upstream documents conversion from millimetres/Z-up to metres/Y-up |
| Bounds | No scene-wide bounds are stored; decoded mesh bounds are computed at runtime |

The root node groups are named `skin`, `skeleton`, `muscles`, `organs`,
`vessels`, and `nerves`. At load time the viewer measures the scene bounds,
centers the model, and scales its height to 3.1 viewer units. The initial
camera looks toward the model from the positive-Z side; no extra rotation is
applied. The leaf mesh-node names correspond to the named structures in the
region-mapping table.

## Verified region mapping

The following exact mesh identifiers were found in the GLB. The viewer groups
matching meshes for selection and highlighting. Left/right labels follow the
upstream `_l` / `_r` suffixes, not screen position.

| Region | Status | Verified mesh identifiers / mapping |
|---|---|---|
| Brain / head | Verified | `brain`, `brainstem`, `cerebellum`, `skull`, `eye_l`, `eye_r`, `cranial_nerves` |
| Heart | Verified | `heart`, `coronary_arteries` |
| Left lung | Verified | `lung_l` |
| Right lung | Verified | `lung_r` |
| Abdomen | Partial | No single abdomen mesh; grouped named structures include `liver`, `colon`, `small_intestine`, `stomach`, `appendix`, `gallbladder`, `spleen`, and `bladder` |
| Left arm | Verified | Side-suffixed arm structures including `upper_arm_muscles_l`, `forearm_muscles_l`, `forearm_l`, `hand_muscles_l` and `hand_l` |
| Right arm | Verified | Side-suffixed arm structures including `upper_arm_muscles_r`, `forearm_muscles_r`, `forearm_r`, `hand_muscles_r` and `hand_r` |
| Left hand | Verified | `hand_muscles_l`, `hand_l`; included in left-arm selection |
| Right hand | Verified | `hand_muscles_r`, `hand_r`; included in right-arm selection |
| Left leg | Verified | Side-suffixed structures including `lower_leg_l`, `foot_l`, and `foot_muscles_l` |
| Right leg | Verified | Side-suffixed structures including `lower_leg_r`, `foot_r`, and `foot_muscles_r` |

The abdomen is marked partial because it is a useful group of individual
organs, not one anatomical mesh. The GLB contains separately selectable
structures; direct clicking can be obstructed by outer geometry, so the
viewer also provides a region selector. Regions without a mapped mesh are
disabled rather than presented as selectable.

## Synthetic demo alert visualization

The frontend preserves ten local scenarios, including global vital alerts,
localized limb markers, and multiple simultaneous markers. Its configurable
demo thresholds compare heart rate, SpO₂, and respiration against the example
baseline in `frontend/src/healthAlerts.js`. The UI threshold editor changes
warning and critical deviation thresholds for these examples; these values
are illustrative settings, not clinical limits.

Heart-rate, SpO₂ and respiration threshold events remain global and never
highlight a heart, lung or limb. All anatomical highlights require explicit
localized synthetic markers. Active mapped regions can be selected from their
on-model marker or the anatomical-region selector. Warning/critical colors
restore to the normal display when a scenario or threshold no longer produces
an alert.

These regional markers are frontend-only demonstrations, separate from ML
predictions and backend outputs. The existing LIVE API / ML integration remains
available but supplies no localized regional measurements. No clinical
threshold or diagnosis is represented.

## Loading, camera, and appearance

`frontend/src/AnatomyModel.jsx` fetches the local GLB once and configures the
installed Three.js `GLTFLoader` with its bundled `MeshoptDecoder`. Loading,
missing-file, and decoding failures have visible status text and a
non-anatomical schematic fallback. A successful load replaces that fallback.

Each cloned mesh receives its own material copy before appearance changes.
The skin is kept faint and transparent so internal structures remain visible;
the outer, anatomy, and wireframe modes vary opacity and wireframe rendering.
Selecting a region highlights its mapped meshes and focuses the camera on the
center of their computed bounds. The region selector also makes internal
structures accessible when an outer layer intercepts a pointer click. Orbit
controls support mouse/touch rotation and panning, zoom, damping, and reset.

The GLB contains approximately one million triangles. The viewer keeps the
provided detail and does not benchmark frame rate on low-end hardware. Mesh
frustum culling is enabled and cloned materials are disposed when the viewer
unmounts. Production build output also reports a JavaScript chunk over Vite's
500 kB advisory threshold; this is a bundle-size warning, not a build failure.

## Measurement and clinical limitations

The model is an educational anatomical visualization. Selection does not
provide organ-specific health measurements. Heart rate, SpO2, temperature, and
respiration remain synthetic demonstration values; the interface does not
claim live astronaut data or clinical validation.

## Validation

Verified for this integration:

- `npm.cmd --prefix frontend run lint` passes.
- `npm.cmd --prefix frontend run build` passes, with the bundle-size advisory
  noted above.
- The Vite development page loaded the local GLB with no decoding error.
- Browser checks confirmed region selection by the selector and a direct
  heart-mesh click, the left-arm/right-leg groups, wireframe/anatomy modes,
  zoom controls, reset, and preservation of the four existing biometric
  cards.
- The older integration log recorded a `THREE.Clock` deprecation and a React
  initialization error. Current layer QA records no uncaught JavaScript
  exceptions; the dependency clock deprecation remains a warning.

Repeat these checks after future changes to the asset or viewer.

## Current layer and organ improvements

See [the current layer QA report](anatomy-layer-improvements.md) and
[complete named mesh inventory](anatomy-mesh-inventory.json). MUSCLES retains
the real skull/jaw as transparent head references because dedicated face/scalp
muscles are absent. ORGANS retains all 34 organ-group meshes and a non-pickable
body outline. Individual organs now have measured focus points and named
selection/details; brain components remain grouped as Brain. Selecting Head
or Brain reveals the existing brain through transparent head structures.

Layer dots describe only explicit markers on meshes actually available in
that layer. A persistent localized/global summary remains visible even when
the affected region is hidden by a layer. The details panel can add or clear
explicit demonstration markers for a selected available structure; changing
the scenario clears added markers and preserves all ten original scenarios.
Cyan is an unmarked demo reference, not a regional health verdict. Grey is
used for unknown regional data in LIVE API MODE.
