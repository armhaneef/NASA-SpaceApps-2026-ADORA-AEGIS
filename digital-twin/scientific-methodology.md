# Digital Twin Scientific Methodology and Limitations

**Owner:** Member 6 - Digital Twin & Research  
**Audience:** AEGIS project contributors  
**Status:** Scientific design guidance, not an implemented model or clinical
digital twin.

## What the current prototype can represent

The current AEGIS project separates a digital-twin visualization from the
data, API, and ML modules. At this stage, the Digital Twin directory contains
placeholders rather than a working anatomy renderer or a physiological
simulation. The dashboard's example values are fabricated. The project does
not currently demonstrate an individualized, continuously updated, clinically
validated human model.

For scientific communication, distinguish:

1. **Anatomical visualization:** A static or interactive licensed 3D asset.
   Its shape illustrates anatomy; it is not a scan of a crew member.
2. **Data-linked visualization:** UI elements display values supplied by an
   identified source. A connection alone does not make the display a validated
   twin or the data clinically meaningful.
3. **Physiological model:** A mathematical model that estimates an internal
   state from specified inputs. It needs justified assumptions, calibration,
   validation, uncertainty, and an intended-use boundary.
4. **Individual digital twin:** A model linked to an individual's longitudinal
   measurements and context, with controlled identity/provenance, update
   rules, verification, validation, privacy, and governance. This is not
   established by a generic avatar plus synthetic vitals.

## Recommended scientific workflow

1. **Define intended use.** For the present demo, constrain use to education
   and interface demonstration. Do not imply screening, diagnosis, prediction,
   treatment, or mission fitness.
2. **Define the observable.** Name each actual input, unit, source, timestamp,
   method, quality, and context. Keep an unmeasured state unavailable.
3. **Preserve provenance.** Separate synthetic examples, measured inputs,
   transformed features, and model outputs. Carry provenance through storage,
   API, visualization, exports, and AI explanations.
4. **Separate evidence from mechanism.** Label direct observations,
   hypotheses, associations, and unknowns differently. A plausible
   mechanism is not proof of an individual's physiological state.
5. **Represent uncertainty and missingness.** Show unavailable, stale,
   simulated, or low-quality data distinctly; do not interpolate or default
   to normal unless an approved method explicitly requires and labels it.
6. **Map anatomy honestly.** Verify the model's actual mesh hierarchy and
   asset rights. A body region may be a broad visual selection, not an
   organ-specific measurement target.
7. **Validate in stages.** Validate schema and unit behavior, then data
   quality, model performance on appropriate independent evidence, and
   finally usability and safety of the display. Passing a UI test does not
   validate a physiological model.
8. **Govern changes.** Version datasets, preprocessing, model, asset,
   thresholds (if ever clinically authorized), and display copy. Maintain a
   human review and correction path for consequential interpretation.

## Prohibited scientific shortcuts

- Do not infer organ health from body-part selection, mesh highlighting, or
  generic systemic vitals.
- Do not call synthetic data "NASA data," real-time telemetry, or an
  astronaut's record.
- Do not claim a physiological twin, a clinical normal range, risk score,
  diagnosis, or operational alert without validated evidence and explicit
  authority.
- Do not treat a reference paper's cohort mean or a dataset's labels as a
  personalized baseline.
- Do not treat association, mechanism, or simulation output as causal proof.
- Do not treat lack of a measured warning as evidence of no risk.

## Current limitations

- The repository's dashboard data are synthetic demonstration values; no
  authenticated sensor or NASA telemetry source is connected.
- The repository data contracts are starter examples and currently have
  distinct nested JSON and flat CSV/JSON shapes.
- No neurological, ocular, vestibular, muscle, bone, abdominal/metabolic,
  immune, radiation-dose, or sleep assessment is connected.
- No medically validated astronaut baseline, thresholds, reference cohort,
  risk calibration, or escalation protocol is defined.
- No model-specific validation or clinical review is complete.
- No GLB/GLTF file or mesh-to-region map is present in this worktree.
- Dataset access and license are record-specific; no NASA dataset has been
  selected or ingested into AEGIS.

## Required disclosure

Suggested project disclosure:

> AEGIS is an educational software prototype. The current health readings are
> synthetic examples. The anatomy display, if enabled, is an illustration and
> is not an individual's medical scan. The prototype is not a medical device,
> does not assess or diagnose health, and must not be used for clinical,
> flight, or mission decisions.

## Related research

- [Astronaut physiology research](../docs/astronaut-physiology-research.md)
- [NASA scientific datasets](../docs/nasa-scientific-datasets.md)
- [Anatomical region science](../docs/anatomical-region-science.md)
- [Cross-team scientific handoff](../docs/cross-team-scientific-handoff.md)
- [Synthetic health data guidance](../docs/synthetic-health-data-guidance.md)

