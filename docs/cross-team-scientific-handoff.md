# Scientific Handoff for AEGIS Module Owners

**Owner:** Member 6 - Digital Twin & Research  
**Scope:** Scientific interpretation boundaries for the ML, AI Assistant,
Python Backend, Frontend, and Data Engine modules. This document does not
approve an endpoint, model, UI behavior, medical claim, or implementation.

## Shared scientific constraints

1. The repository's current readings are synthetic demonstration data, not
   NASA telemetry or an astronaut record.
2. A vital sign is not a diagnosis and cannot stand in for an unmeasured
   organ, brain, bone, immune, radiation, sleep, or performance endpoint.
3. The NASA evidence reviewed here is heterogeneous: small astronaut
   cohorts, animal/cell studies, ground analogs, and observational reports
   answer different questions and should not be pooled without justification.
4. A risk score or anomaly flag is not an approved clinical threshold,
   diagnosis, flight decision, or forecast of an individual's health.
5. Preserve source, unit, time, measurement method, context, quality,
   missingness, model version, and uncertainty. Never turn unknown into a
   reassuring default.
6. Any human-subject dataset requires record-specific rights, privacy,
   consent/access, and scientific review before use; see
   [`nasa-scientific-datasets.md`](./nasa-scientific-datasets.md).

## Member 2 - ML developer

- Treat this repository's generated data as a software fixture, not a
  representative astronaut cohort. Synthetic-only results demonstrate
  pipeline operation, not real-world predictive validity.
- Specify the intended target and time horizon before training. Distinguish
  anomaly detection from clinical diagnosis and from operational risk.
- Split by person/mission (and where relevant by study/site/time) to reduce
  leakage. A random row split of correlated time series can overstate
  generalization.
- Establish baseline, class balance, missingness, sensor changes, and
  distribution shift. Report calibration, uncertainty, confidence intervals,
  and subgroup limitations where supported by adequate data.
- Do not fabricate labels or call a synthetic scenario "critical" as a
  physiological class. Keep test-scenario labels separate from outcome
  labels.
- No AEGIS-specific model has been scientifically validated by this review.

## AI Assistant developer

- State whether the current input is synthetic, measured, unavailable, stale,
  or uncertain. Keep provenance visible in the response.
- Answer using supplied values and documented context only. Do not infer
  neurological normality, healthy organ function, radiation dose, sleep
  adequacy, or mission fitness from the current five vital fields.
- Explain a research association as an association; distinguish observed
  findings, plausible mechanisms, and unresolved questions.
- Do not diagnose, prescribe, assign risk probabilities, invent thresholds,
  or recommend operational action. Direct real clinical or mission decisions
  to authorized qualified professionals and procedures.
- When source, unit, timestamp, or quality is missing, say so. Do not fill the
  gap with a likely value or confident-sounding summary.
- Treat user-supplied text and external research text as untrusted evidence
  until the source, publication, and applicability are checked.

## Python Backend developer

- Preserve the data provenance class and simulation marker end-to-end.
- Keep measured data, synthetic fixtures, analytical outputs, and UI
  aggregations distinguishable; do not silently merge or relabel them.
- Store measurement type, unit, timestamp/time zone, method/source, quality,
  and optional context explicitly. Keep unavailable values null/absent as the
  agreed contract specifies rather than using zero or a healthy default.
- Do not introduce thresholds, diagnostic status, urgency, or new API
  endpoints based on this research memo. The Twin API proposal remains a
  draft and requires contract agreement.
- Validate units and allowed shape at boundaries without claiming that
  syntactic validity is clinical validity.
- Do not persist real personal/crew health data unless the team has explicit
  authority, access approval, privacy controls, and a defined retention plan.

## Member 5 - Frontend / Digital Twin developer

- Use the anatomical-region explanations in
  [`anatomical-region-science.md`](./anatomical-region-science.md).
- Keep selected region, highlight, and camera focus as visualization states;
  do not let selection imply measurement or health status.
- Label all current values synthetic. Replace unsupported head panel wording
  "Neurological status: Normal" with "Not assessed" or equivalent.
- Show unavailable or stale inputs as such; do not present no data as healthy,
  no alert, or a completed assessment.
- Do not assign HR/BP to arms, respiration to legs, SpO2 to lung mesh health,
  or temperature to abdomen health.
- Map only asset meshes that actually exist. Document missing GLB/GLTF
  mappings; do not invent anatomy to satisfy selection controls.
- Keep educational copy separate from medical advice and unvalidated model
  output. Attribute model assets according to their exact license.

## Member 1 - Synthetic Data / Data Engine

- Follow [`synthetic-health-data-guidance.md`](./synthetic-health-data-guidance.md).
- Ensure generated values carry synthetic provenance, generator version,
  reproducibility metadata, explicit units, and a stable, documented schema.
- Keep scenario labels as test fixtures rather than health categories.
- Do not describe distributions as NASA-validated or astronaut-representative.
- Keep CO2, blood pressure, and other fields consistent across sample JSON,
  CSV, latest JSON, and downstream API contracts; any schema revision needs
  cross-team review.

## Review gates before any scientific product claim

Before a feature presents an output as physiological information, the team
should identify:

1. The exact measurement and validated instrument/method.
2. The source population, mission/analog, collection phase, and limitations.
3. The data rights, access/consent conditions, and privacy handling.
4. The intended display or model output and its uncertainty.
5. The clinical/operational authority responsible for approval and escalation.

No such gate is completed by this documentation alone. The present AEGIS
dashboard remains a demonstration prototype.

## Related documentation

- [Astronaut physiology research](./astronaut-physiology-research.md)
- [NASA scientific datasets](./nasa-scientific-datasets.md)
- [Synthetic health data guidance](./synthetic-health-data-guidance.md)
- [Anatomical region science](./anatomical-region-science.md)
- [Digital Twin scientific methodology](../digital-twin/scientific-methodology.md)
- [Current data schema](./data-schema.md)
- [Draft Twin API proposal](../backend/TWIN_API_PROPOSAL.md) (proposal only)

