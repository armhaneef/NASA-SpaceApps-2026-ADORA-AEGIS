# Verified anatomical asset

The viewer uses the included `adora-anatomy.glb` (7,614,076 bytes), sourced
previously from open-anatomy-3d 0.1.0 / BodyParts3D under CC BY 4.0. The existing
on-screen attribution is preserved. No replacement model is downloaded.

The asset contains 128 meshes: skin 1, skeleton 28, muscles 41, organs 34,
vessels 22 and nerves 2. It requires meshopt decoding and mesh quantization,
handled by Three.js's bundled loader/decoder. Runtime bounds center the asset
and apply one uniform scale; organs retain their original positions/scales.

MUSCLES includes real neck muscles and retains the existing skull, mandible,
teeth and eyes as transparent references. Dedicated face/scalp muscles are
absent. ORGANS includes the verified brain, brainstem, cerebellum, heart, both
lungs, liver, both kidneys, stomach and other named organ meshes, with a faint
non-pickable body outline. The skin's decoded runtime name is `skin_1` because
the parent group is also named `skin`; layer classification uses ancestry.

Exact mappings live in `src/anatomyRegions.js`; availability and focus bounds
come from the actual loaded scene. Missing structures are marked unavailable.
A missing/invalid asset shows a clearly labelled non-anatomical schematic.
Adding absent geometry requires a licensed, reviewed, aligned mesh and matching
selection/layer metadata; it must not be fabricated from global vital signs.

Only explicit localized synthetic markers color anatomical geometry. Cyan is
an unmarked demo reference, yellow warning, red critical; grey represents
unknown regional data in LIVE API MODE. No regional sensor or diagnosis is
implied by the mesh, its color, or selection.

See `docs/anatomical-model-integration.md` for provenance and
`docs/anatomy-layer-improvements.md` for the current inventory and QA record.
