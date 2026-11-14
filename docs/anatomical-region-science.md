# Anatomical Region Science for the AEGIS Digital Twin

**Audience:** Member 5 - Frontend / Digital Twin  
**Owner:** Member 6 - Digital Twin & Research  
**Purpose:** Provide conservative educational descriptions for selectable
body regions. This is not a clinical mapping specification or a claim that
the current model contains separately measurable organs.

## General rules

- The 3D figure is an anatomical visualization, not an identified astronaut's
  body, scan, or personalized physiological model.
- A selectable region is a navigation/highlight target. Selection alone
  reports no clinical state.
- Keep "education," "synthetic demo value," and "measured health information"
  visibly distinct.
- Do not map systemic readings to local anatomy unless the measurement
  actually supports that interpretation. The current demo readings do not
  provide organ-specific assessment.
- Preserve the model's real anatomy and mesh names. Do not manufacture
  internal organ meshes, substitute primitives, or imply a hidden organ is
  present. Document unimplemented mappings until a suitable licensed asset is
  present and its actual mesh names have been inspected.
- Define left/right from the represented person's anatomical perspective;
  verify the viewer-facing orientation and label it consistently.
- Any real-model source, attribution, and license requirements must be
  verified before bundling or changing assets.

## Region descriptions and current-data limits

| Selectable region | Educational explanation | What the current synthetic dashboard can say |
|---|---|---|
| Head / Brain | The brain integrates vestibular, visual, and body-position cues. Microgravity changes the sensory environment; some long-duration astronauts show ocular findings discussed as SANS. Its mechanisms and individual outcomes remain under study. The eye is not the brain, and SANS is not a generic brain-disease label. | Nothing about brain function, vision, balance, intracranial pressure, or SANS. The displayed synthetic demo metrics do not assess these outcomes. |
| Heart | The heart circulates blood through the body. Gravity, posture, activity, mission phase, and individual adaptation affect how cardiovascular measurements should be interpreted. | A fabricated HR value only. A single synthetic HR is not a cardiac examination, output, diagnosis, or individual baseline. |
| Lungs | The lungs exchange oxygen and carbon dioxide. Gravity affects pulmonary ventilation/perfusion distribution and related research measurements. | Fabricated SpO2 and respiration-rate fields only. They are not a lung function test, blood gas, respiratory waveform, or evidence of normal pulmonary health. |
| Abdomen | This is a body region containing multiple organs, not one organ or one physiological system. Nutrition, fluid distribution, body composition, and organ function require different measurements. | No abdominal-organ, metabolic, renal, hepatic, pancreatic, or gastrointestinal assessment. A synthetic temperature is systemic demo data, not an abdomen reading. |
| Left arm | The arm contains bone, muscle, joints, nerves, and vessels; limb loading and function are studied in spaceflight physiology. | No local strength, bone density, circulation, nerve, or joint measurement. Blood pressure is not in the shared backend/data-engine contract; any local mock value would be systemic UI context, not an arm measurement. |
| Right arm | Same broad systems as the left arm; side-specific differences require side-specific observations and method context. | No right-arm-specific measurement. Do not duplicate systemic readings as if separately collected. |
| Left leg | Lower-limb bone and muscle are relevant to mechanical unloading, exercise countermeasures, locomotion, and postflight adaptation. | No local muscle size/strength, bone density, gait, or limb function data. Respiratory rate is not a leg measurement. |
| Right leg | Same broad systems as the left leg; side-specific claims require side-specific measurements. | No right-leg-specific measurement. Do not imply symmetry or a side-specific result from the whole-body demo feed. |

## Suggested interface wording

Use the following as unvalidated educational copy, not a health result:

> **Spaceflight physiology context:** Select a region to explore relevant
> research. Region selection and the 3D highlight are illustrative. The
> current readings are synthetic and do not measure local organ function.

For unavailable region-specific data, prefer:

> **Not assessed:** No region-specific measurement is connected in this demo.

Avoid "Normal," "Stable," "Healthy," "within expected range," and
"Neurological status: Normal" unless those are explicitly defined as
non-clinical UI states and cannot be mistaken for an assessment. The current
head panel's "Neurological status: Normal" is not supported by the available
synthetic fields and should be corrected by the frontend owner.

## 3D mapping checklist for Member 5

1. Inspect the selected GLB/GLTF file and record its actual node and mesh names.
2. Map only existing, anatomically supported selectable meshes to the region
   list; disclose when an item is a broad body-region proxy rather than a
   separately modeled organ.
3. Verify model orientation, left/right, scale, origin, and camera framing
   from the asset itself.
4. Do not describe a highlighted surface mesh as an internal organ unless the
   model actually represents that organ.
5. Keep highlight state and camera animation independent of health status.
6. Add the source and exact license/attribution required by the asset owner.
7. Test missing, loading, and failed-asset states without substituting
   invented anatomy.

The current `origin/dev` includes a stylized renderer and the
[`adora-anatomy.glb` asset](../frontend/public/models/adora-anatomy.glb).
The [Member 5 integration report](./anatomical-model-integration.md)
documents inspected mesh identifiers and software-level region mappings,
including the abdomen's partial grouping. This research document has not
independently verified the asset's anatomical accuracy or clinically
validated the mappings. Member 5 owns GLB loading, mesh mapping, and viewer
behavior; these implementation details do not establish that the prototype
measures regional health.

## Research references

- [Brain and nervous-system evidence](./astronaut-physiology-research.md#phase-1-brain-and-nervous-system)
- [Respiratory and musculoskeletal evidence](./astronaut-physiology-research.md#phase-2-remaining-astronaut-physiology-systems)
- [Scientific references index](./scientific-references.md)
