# Anatomy layers and regional markers — 2026-11-15

Implemented in the existing `feature/aegis-final-full-integration` checkout.
The anatomy and marker improvements are committed at
`37e2dddd6af62c9d08696e32939a7f1e8ae1942a`, based on integration commit
`743aa11c9155c36c7889b0f9c8ae1870b054d6af`. Earlier versions of this report
described the pre-commit worktree; that historical status is superseded here.
The later security/documentation correction pass is uncommitted for review.
No push, merge, PR #15 change, private environment-file change, replacement
model download or live Gemini request was made by the correction pass.

## Verified asset availability

The existing `frontend/public/models/adora-anatomy.glb` is unchanged:

- 7,614,076 bytes; 134 nodes; 128 meshes; 1,026,032 triangles.
- SHA-256: `25248bef02f0ca43eedbd25231f8b6f9681865a57016f9d5e352d407407336c7`.
- Existing open-anatomy-3d / BodyParts3D attribution and CC BY 4.0 are retained.
- [Complete named inventory](anatomy-mesh-inventory.json), extracted from the
  local GLB; tests also decode the actual meshopt-compressed geometry.

| Group | Meshes | Availability |
|---|---:|---|
| Skin | 1 | Whole-body spatial outline; not a segmented surface |
| Skeleton | 28 | Skull, mandible, teeth, cervical/thoracic/lumbar spine, bilateral arm/hand/leg/foot bones and other named bones |
| Muscles | 41 | Torso, both neck muscle groups, arms/hands, thighs/calves/shins/feet and other named muscle groups |
| Organs | 34 | All original named organ-group meshes retained |
| Vessels | 22 | Original named vessel structures retained in FULL BODY |
| Nerves | 2 | `spinal_cord`, `cranial_nerves` retained in FULL BODY |

These are **34 organ-group meshes, not 34 distinct organs**: named groups can
contain composite structures, and brain components share one selection.
The 34 organ-group mesh names are:

```text
lung_r, brain, heart, liver, appendix, colon, cerebellum, eye_l, eye_r,
gallbladder, reproductive, larynx, small_intestine, esophagus, lung_l,
adrenal_l, tongue, brainstem, pharynx, kidney_l, thymus, bronchi,
salivary_glands, ureter_l, pancreas, pituitary, prostate, adrenal_r,
kidney_r, ureter_r, spleen, stomach, trachea, bladder
```

Brain, brainstem and cerebellum share the Brain selection. Other organs have
their own exact mesh selections, including separate kidneys, lungs and eyes.
All 34 organ-group meshes receive picking metadata; browser tests exercised an
actual heart-mesh click and selection/focus of the required major organs.
Organs remain at their original positions and proportions. Posterior organs
such as kidneys can overlap others from the front; selection reduces other
organs' opacity and rotation remains available.

## Layers, focus and truthful limitations

- **MUSCLES:** all 41 actual muscle meshes remain visible. The existing skull,
  mandible, teeth and eyes provide a translucent head reference. Both actual
  `neck_muscles_l` and `neck_muscles_r` remain visible.
- **ORGANS:** all 34 organ-group meshes are visible with a faint, non-pickable
  whole-body outline. This outline cannot intercept clicks intended for organs.
- **HEAD / BRAIN:** the verified brain components appear through transparent
  skull/head references. Bounds determine focus and distance; no organ geometry
  is translated or resized independently. Smooth transitions stop when the user
  starts orbit interaction or explicitly zooms. Reduced motion uses immediate
  focus and demand rendering. Desktop stage height stays stable as details grow.
- Full body, skeleton, wireframe, labels, scan, zoom, pan and reset remain.
  Mobile limits canvas pixel ratio to 1. Materials update before rendering to
  avoid a wrongly colored first frame, without recompiling on every selection.
- **Unsupported:** no dedicated facial/scalp muscle meshes and no single
  standalone abdomen mesh. The abdomen is an educational group of real named
  structures. Hands, bones and neck are actual model geometry, not fabricated
  muscle replacements. The skin is one mesh and cannot be highlighted as a
  separate arm/leg surface; localized colors follow the verified underlying
  regional muscle/bone/vessel meshes.
  The broad `shoulder_muscles_l/r` assemblies span neck and torso geometry, so
  they remain visible but unmarked. Deltoids, rotator cuffs and the verified
  arm/forearm/hand meshes retain arm coloring without spreading into the torso.
- Missing or invalid model files show the labelled schematic fallback and
  unavailable options. A test fixture with the brain components omitted shows
  “BRAIN MESH UNAVAILABLE” while retaining the useful real head view.
  Adding absent structures requires licensed, compatible, aligned geometry,
  reviewed names/layer metadata and availability tests.

## Regional marker behavior

All ten existing scenarios are preserved. The details panel adds an explicit
marker editor for the selected available region/organ in DEMO MODE, allowing
left-leg warnings and organ-specific markers without replacing a scenario.
Added markers coexist and are scoped by astronaut ID. Each astronaut has an
independent custom-marker count and regional colors. Adding, editing severity
or clearing a marker changes only the selected astronaut's custom bucket.
Switching from A-01 to A-02 does not inherit A-01's markers; returning to A-01
restores its markers during the current application session. These overlays
are not persisted to the backend or across page reloads.

Changing the scenario clears only the selected astronaut's custom overlay;
other astronauts retain their buckets. The explicit scenario remains a global
demo choice and is not an astronaut-specific sensor record. Selection, all
four anatomy layers and camera reset preserve the selected astronaut's markers.
Global vital-sign or ML anomalies are never converted to localized markers.

The mobile details drawer includes visible keyboard-focusable summaries and
excludes closed-details contents, hidden/disabled/inert controls and negative
tab stops. Tab and Shift+Tab wrap inside the modal in both directions, with
focus containment even after a programmatic outside-focus attempt. Close,
Escape, backdrop and touch closure restore the opener (or available toggle).
Both collapsed and expanded marker editors are covered by browser regressions.

Colors: cyan normal/unmarked **demo reference**, yellow warning, red critical,
neutral grey for unknown regional data in LIVE API MODE. Cyan never certifies
normal regional health: every details view explicitly states that no regional
sensor reading is supplied. Only localized synthetic markers set yellow/red
anatomical colors. Global heart-rate, SpO2, respiration and ML findings do not
localize to any organ or limb.

Layer dots depend on actual loaded mesh coverage. A right-arm critical marker
lights FULL BODY, SKELETON and MUSCLES, and does not light ORGANS. An individual
liver marker lights the available organ layer and does not color the stomach or
imply a skeleton finding. A persistent count remains visible when a layer hides
the affected region. Global findings have a separate count.

Details show selected structure, severity, scenario, explicit observation,
regional sensor absence, source, mesh availability and limitations. Marker
controls are absent in LIVE API MODE. Astronaut selection, four metrics, charts,
central backend integration, ML display, AI Assistant, disclosures, mobile
drawer and keyboard access are retained.

## Validation

| Check | Result |
|---|---|
| Existing plus new frontend tests | **46 passed**, 0 failed, skipped or cancelled |
| Main desktop/mobile Chrome suite | **25 passed** |
| Additional camera, controls and missing-brain browser checks | **5 passed** |
| Independent drawer and astronaut-marker browser regressions | **23 passed in one clean execution**, 0 failed/skipped |
| `npm.cmd --prefix frontend run lint` | Passed |
| `npm.cmd --prefix frontend run build` | Passed |
| `git diff --check` | Passed |

This table records the independently executed pre-correction anatomy review at
`37e2ddd`. The 23-check regression harness is tracked at
`frontend/tests/reviewFindings.browser.mjs`; it tests actual focus targets,
independent counts, actual mesh colors, edit/removal isolation, layer/camera
reset semantics and all ten scenarios. The 30 other anatomy checks and these
23 checks were not rerun during the later CORS/documentation correction pass;
frontend source/model files were unchanged. See the
[current integration QA record](aegis-final-integration-qa.md) for that pass's
personally rerun tests, distinct from this retained browser evidence.

Tests cover decoded asset availability, layers, unchanged organ transforms,
head references, individual markers, multiple markers, global-only alerts,
grey unknown data, missing brain/model, smooth and reduced-motion focus,
zoom/rotation/pan/reset, layer indicators, actual picking, desktop/mobile
layout, regional provenance and retained dashboard features.

Browser: Chrome with WebGL/SwiftShader; desktop 1440x1050 and mobile 390x844.
No uncaught JavaScript exceptions or model API requests occurred. Browser AI
requests were explicitly blocked or mocked; this is not Gemini verification.
Backend, ML and AI implementation files were not changed by this task.

Screenshots and machine-readable results are local under
`.integration/anatomy-qa/` in the original workspace:

- `muscles-desktop.png`, `organs-desktop.png`, `brain-desktop.png`
- `right-arm-critical-desktop.png`, `liver-critical-desktop.png`
- `muscles-mobile.png`, `regional-details-mobile.png`
- `missing-brain-reference.png`
- `browser-results.json`, `extra-browser-results.json`

The local QA harnesses are `.integration/anatomy-browser.cjs` and
`.integration/anatomy-extra-browser.cjs`, outside the tracked checkout. These
harnesses and screenshots are review artifacts, not application dependencies.

The existing large-bundle build warning remains (about 1.66 MB minified /
465 kB gzip), as does the dependency `THREE.Clock` deprecation. The asset has
over a million triangles; low-end mobile hardware frame rate is not benchmarked.
No physical regional sensors or clinical validation are provided.

## Historical anatomy change manifest

1. `frontend/src/AnatomyModel.jsx`
2. `frontend/src/anatomyScene.js` (new)
3. `frontend/src/anatomyRegions.js`
4. `frontend/src/healthAlerts.js`
5. `frontend/src/App.jsx`
6. `frontend/src/App.css`
7. `frontend/tests/anatomyScene.test.js` (new)
8. `frontend/tests/healthAlerts.test.js`
9. `frontend/public/models/README.md`
10. `docs/anatomical-model-integration.md`
11. `docs/anatomy-mesh-inventory.json` (new)
12. `docs/anatomy-layer-improvements.md` (this report)

The original 12-file manifest above describes the anatomy implementation.
Commit `37e2ddd` also includes `frontend/tests/reviewFindings.browser.mjs` and
the two reviewed fixes in `frontend/src/App.jsx`. It is no longer an
uncommitted anatomy patch. The current correction pass remains unstaged and
uncommitted pending independent review and approval; no Git delivery is
authorized by this report.
