# Shared sensor record schema

The sample at [`../data/synthetic/sample_reading.json`](../data/synthetic/sample_reading.json)
demonstrates the initial JSON shape. It is fabricated solely to demonstrate
field names and units; it is not NASA data or a real person's measurement.

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
