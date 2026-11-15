# Shared sensor record schema

The sample at [`../data/synthetic/sample_reading.json`](../data/synthetic/sample_reading.json)
demonstrates the initial JSON shape. It is fabricated solely to demonstrate
field names and units; it is not NASA data or a real person's measurement.

## Synthetic data-engine output

The generator in
[`../data-engine/generators/generate_synthetic_data.py`](../data-engine/generators/generate_synthetic_data.py)
exports a flat record to `data/synthetic/astronaut_vitals.csv` and writes the
latest record to `data/synthetic/latest_vitals.json`. The CSV column names and
JSON keys match:

| Field | Type | Unit / meaning |
|---|---|---|
| `astronaut_id` | string | Fabricated identifier; defaults to `AST-001`, can be overridden |
| `timestamp` | string | ISO 8601 UTC timestamp (`Z`), one-minute intervals |
| `heart_rate_bpm` | integer | Simulated heart rate in beats per minute |
| `spo2_percent` | number | Simulated oxygen saturation in percent |
| `body_temperature_c` | number | Legacy synthetic body-temperature field with unspecified skin/core semantics |
| `skin_temperature_c` | number | Separate synthetic skin-temperature feature, degrees Celsius; never derived from `body_temperature_c` |
| `respiration_rate_bpm` | number | Simulated respiration rate in breaths per minute |
| `scenario` | string | `normal`, `warning`, or `critical` demo profile |

Each generated record has the same fields. The JSON file is a single object for
the final reading; the CSV contains the full series. The generator uses a fixed
UTC start time and a configurable random seed for reproducibility. Scenario
bounds are illustrative software-demo constraints only, not clinical ranges or
diagnostic criteria. All values are synthetic and not sourced from NASA or a
real astronaut.

The new `skin_temperature_c` channel is generated independently with a separate
seeded random stream and fixed profile across all three vital-sign scenarios.
Its engineering fixture uses a 31.8 °C center, 0.5 °C spread, and 30.3–33.3 °C
clamp to supply complete input to the existing ML contract. The center is
approximately the wrist wearable cohort mean (89.2 °F) reported by Dunn et al.;
the generated series does not reproduce that study's data, cohort, or method.
The spread and clamp are integration-fixture choices, not reference limits.
That study also reports wrist skin temperature as more variable than oral
temperature, which supports keeping the fields distinct
([Dunn et al., 2021](https://doi.org/10.1038/s41591-021-01339-0)). This fixture
has no defined collection site, sensor model, environmental
correction, calibration, or physiological validity. It is not used to infer a
condition, scenario severity, or anatomical state.

This flat generator contract is separate from the nested demonstration
`sample_reading.json` format below; consumers should select the contract they
are integrating with rather than assume the two shapes are interchangeable.

### Backend adapter mapping

`data-engine/adapters/backend_ingest.py` adapts each generated record to the
backend's existing grouped `POST /health/ingest` contract. It supplies
`sensor_type: "synthetic_multi_sensor"`, `data_source: "synthetic_data_engine"`,
`is_simulated: true`, and `quality: "synthetic_demo"`, then maps:

| Generator field | Backend measurement | Unit |
|---|---|---|
| `heart_rate_bpm` | `heart_rate` | `bpm` |
| `spo2_percent` | `spo2` | `%` |
| `skin_temperature_c` | `skin_temperature` | `degC` |
| `respiration_rate_bpm` | `respiration_rate` | `breaths/min` |

The adapter deliberately omits `body_temperature_c`; its meaning remains
unspecified and is not silently converted. Only the new, explicitly named
synthetic `skin_temperature_c` maps to the backend `skin_temperature` field.
The grouped ingestion schema accepts this additive field and stores it with the
same timestamp and synthetic provenance as the other readings.

| Field | Type | Meaning |
|---|---|---|
| `astronaut_id` | string | Synthetic identifier; must not identify a real person |
| `timestamp` | string | ISO 8601 timestamp, preferably UTC (`Z`) |
| `heart_rate` | object | `value` and `unit` (`beats/min`) |
| `spo2` | object | `value` and `unit` (`%`) |
| `temperature` | object | `value` and `unit` (`degC`) |
| `skin_temperature` | object | `value` and `unit` (`degC`); distinct from `temperature` |
| `respiration_rate` | object | `value` and `unit` (`breaths/min`) |
| `co2` | object | `value` and `unit` (`ppm`) |
| `data_source` | string | Provenance label; the included fixture uses `synthetic_example` |

Each measurement object contains a numeric `value` and explicit string `unit`.
Consumers should preserve the unit and provenance, validate values and
timestamps at their boundaries, and avoid silently substituting missing data.
This initial example does not define clinical thresholds, allowed ranges,
sampling frequency, or a validated data-collection protocol; those decisions
require separate review before implementation.
