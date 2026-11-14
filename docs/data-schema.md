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
| `astronaut_id` | string | Fabricated identifier; currently always `AST-001` |
| `timestamp` | string | ISO 8601 UTC timestamp (`Z`), one-minute intervals |
| `heart_rate_bpm` | integer | Simulated heart rate in beats per minute |
| `spo2_percent` | number | Simulated oxygen saturation in percent |
| `body_temperature_c` | number | Simulated body temperature in degrees Celsius |
| `respiration_rate_bpm` | number | Simulated respiration rate in breaths per minute |
| `scenario` | string | `normal`, `warning`, or `critical` demo profile |

Each generated record has the same fields. The JSON file is a single object for
the final reading; the CSV contains the full series. The generator uses a fixed
UTC start time and a configurable random seed for reproducibility. Scenario
bounds are illustrative software-demo constraints only, not clinical ranges or
diagnostic criteria. All values are synthetic and not sourced from NASA or a
real astronaut.

This flat generator contract is separate from the nested demonstration
`sample_reading.json` format below; consumers should select the contract they
are integrating with rather than assume the two shapes are interchangeable.

| Field | Type | Meaning |
|---|---|---|
| `astronaut_id` | string | Synthetic identifier; must not identify a real person |
| `timestamp` | string | ISO 8601 timestamp, preferably UTC (`Z`) |
| `heart_rate` | object | `value` and `unit` (`beats/min`) |
| `spo2` | object | `value` and `unit` (`%`) |
| `temperature` | object | `value` and `unit` (`degC`) |
| `respiration_rate` | object | `value` and `unit` (`breaths/min`) |
| `co2` | object | `value` and `unit` (`ppm`) |
| `data_source` | string | Provenance label; the included fixture uses `synthetic_example` |

Each measurement object contains a numeric `value` and explicit string `unit`.
Consumers should preserve the unit and provenance, validate values and
timestamps at their boundaries, and avoid silently substituting missing data.
This initial example does not define clinical thresholds, allowed ranges,
sampling frequency, or a validated data-collection protocol; those decisions
require separate review before implementation.
