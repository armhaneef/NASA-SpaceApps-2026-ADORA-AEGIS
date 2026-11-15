# Synthetic Health Data Guidance for AEGIS

**Audience:** Member 1 - Synthetic Data / Data Engine  
**Owner:** Member 6 - Digital Twin & Research  
**Status:** Scientific guidance; implementation changes are out of scope.

## Purpose and boundary

The repository's sample JSON, generated CSV, and dashboard fixtures are
fabricated software-demo inputs. They are not NASA telemetry, measurements
from an astronaut, clinical data, or validated estimates of a flight
population. Their purpose is to exercise display, data flow, and test
scenarios.

Synthetic data can be useful for interface tests and software demonstrations.
It cannot establish medical plausibility, estimate astronaut risk, validate a
clinical algorithm, or support operational/flight decisions merely because it
looks physiologically reasonable.

## Current repository formats inspected

The repository currently has two distinct examples:

- The nested `data/synthetic/sample_reading.json` contains synthetic HR, SpO2,
  temperature, respiration rate, CO2, and `data_source`.
- The generated CSV and latest JSON contain `AST-001` (or a configured
  synthetic identifier), UTC timestamps, synthetic HR, SpO2, the legacy
  `body_temperature_c` field, a separate `skin_temperature_c` feature,
  respiration rate, and a `scenario` value. The generator uses a fixed UTC
  start and configurable seed.

These are not interchangeable schemas. The generated CSV does not include
CO2 or the sample JSON's `data_source`; neither generator output consistently
carries a per-record `is_simulated` flag or measurement-level unit/provenance
fields. Blood pressure is absent from both sample formats, the data-engine
generator, and the shared backend reading contract. The current dashboard
shows four generated synthetic metrics (heart rate, SpO2, body temperature,
and respiration rate), not blood pressure. If a local or older mock UI shows
a blood-pressure value, it is a presentation-only fixture and not a backend
measurement. The generator's scenario labels and bounds are demo controls,
not clinical classes or approved thresholds.

The new `skin_temperature_c` feature is independent of the legacy
`body_temperature_c` field and generated from its own seeded random stream. It
uses one fixed profile across all `normal`, `warning`, and `critical` vital
scenarios, so the feature is not being used to label those scenarios. The
profile is a software-integration fixture, loosely centered on a published
consumer wrist-wearable cohort mean; its spread and bounds are engineering
choices, not astronaut data or clinical limits. See [the data schema](./data-schema.md)
and [Dunn et al. (2021)](https://doi.org/10.1038/s41591-021-01339-0).

The backend adapter omits `body_temperature_c` and maps only the separately
named `skin_temperature_c` to `skin_temperature`. ML consumes that explicit
measurement as its `temperature` feature; the stored measurement name and
legacy field are not changed or inferred.

## Recommended scientific safeguards

1. **Label at every boundary.** Keep `data_source: synthetic_example` and an
   explicit simulated/synthetic marker in all demo responses, derived views,
   downloads, screenshots, and AI prompts. Do not rely on a filename or one
   page-level label to preserve provenance.
2. **Use fabricated identities.** Never use a real astronaut name,
   identifier, mission record, or personal health data in fixtures. Keep
   demo identifiers visibly synthetic.
3. **Keep scenarios semantically technical.** Names such as `normal`,
   `warning`, and `critical` may be retained for UI test coverage only if
   documentation says they are demo states. Prefer neutral test labels such
   as `baseline_demo`, `changed_demo`, or `missing_data_demo` when no
   clinically approved interpretation exists.
4. **Do not label demo values as diagnosis.** Avoid unqualified labels such
   as "normal," "healthy," "stable," "neurological status normal," "low
   risk," or "no alerts." A mock UI state is not a measured clinical
   assessment. Use "synthetic example" and "not assessed" where appropriate.
5. **Keep units, timestamps, and context explicit.** Use ISO 8601 UTC
   timestamps where known; store the unit with each measurement; document
   whether temperature is skin, oral, core, or unspecified; preserve sensor,
   posture/activity, measurement method, and mission phase only when truly
   supplied. Unknown context should be null/unknown, not invented.
6. **Separate missing, invalid, stale, and zero.** Do not replace missing or
   rejected values with fabricated healthy-looking defaults. Keep data
   quality and availability distinct from the measurement and from any
   display alert.
7. **Make generation reproducible.** Retain the seed, generator version,
   scenario configuration, and timestamp policy for a test dataset. Record
   which values are sampled, copied, transformed, or held constant.
8. **Avoid unsupported correlations.** Do not derive organ-specific states
   from generic vitals. Do not create synthetic joint distributions or
   trend patterns and then imply they were observed in flight.
9. **State the intended test.** Each scenario should exercise a software
   behavior (formatting, missing field, unit conversion, chart gap, or
   notification UI), not simulate a medical condition unless the scenario
   has an explicit, reviewed research basis and is still marked synthetic.
10. **Protect downstream consumers.** Keep synthetic data on an explicit
    demo path. ML, backend, frontend, visualization, and AI consumers must
    preserve source and simulation markers rather than silently blending
    examples with future measured data.

## Proposed metadata contract for future review

This is a documentation suggestion, not an approved schema or an
implementation request.

| Metadata | Meaning |
|---|---|
| `data_source` | `synthetic_example`, `measured`, or another explicit provenance class |
| `is_simulated` | Boolean flag; true for every fabricated demo measurement |
| `scenario_id` | Test-scenario identifier only, never a diagnosis |
| `generator_name` / `generator_version` | Reproducible software provenance |
| `seed` | Optional reproducibility value; do not use as a user identifier |
| `measurement_type` | Stable field name with a defined semantic meaning |
| `value` / `unit` | Value with explicit unit; do not infer units from the name |
| `timestamp` | ISO 8601 timestamp and time-zone policy |
| `quality` | Technical availability/quality state, not clinical status |
| `context` | Optional documented collection context; omit or mark unknown when unavailable |

The schema owner should align this with the existing data-engine and backend
contracts before changing code. Do not add a measured/NASA source label to
any current fixture.

## Evidence and validation limits

- A plausible-looking random series is not physiologically validated.
- A distribution copied from a paper is not automatically representative;
  that study's cohort, measurement method, mission, and conditions matter.
- Min/max scenario bounds are not clinical reference ranges.
- A model trained or tested only on synthetic data has no demonstrated
  performance on real crew data.
- Synthetic data cannot remove privacy obligations if it is derived from
  real individuals; disclose derivation and applicable restrictions.
- Clinical or operational use would require an approved data source,
  measurement protocol, representative evidence, suitable validation,
  independent review, and explicit authorization. This prototype has none of
  those approvals.

## Dashboard and shared-contract boundary

The current dashboard's four cards are client-side synthetic demo metrics;
they are not readings supplied by the backend. The shared sample and
data-engine formats contain no blood-pressure field, and the backend sensor
schema does not accept blood pressure as a measurement type. A blood-pressure
value shown in a local or older mock UI (for example, 118/76 mmHg) must remain
identified as a fabricated UI fixture, not a backend measurement or an
astronaut record.

The current frontend identifies the head view as educational and says that no
neurological assessment is provided. Any older/local mock label such as
"Neurological status: Normal" is unsupported and must not be presented as a
finding. The UI owner should keep the explicit "not assessed" limitation
visible; documentation must not imply that these mock states are measured
health data.

## Sources

- Project data contract: [`data-schema.md`](./data-schema.md)
- NASA repository and rights review: [`nasa-scientific-datasets.md`](./nasa-scientific-datasets.md)
- Research limitations: [`astronaut-physiology-research.md`](./astronaut-physiology-research.md)
