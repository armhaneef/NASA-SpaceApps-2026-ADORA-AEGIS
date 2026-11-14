# Data engine

This module generates clearly labeled synthetic astronaut vital-sign time
series for backend, ML, and visualization development. It is separate from the
API and analysis code so each team module can integrate against a small,
documented data contract.

**Inputs:** Reading count, one of the `normal`, `warning`, or `critical` demo
scenarios, and an integer random seed.

**Outputs:** `data/synthetic/astronaut_vitals.csv` with all readings and
`data/synthetic/latest_vitals.json` with the final reading. Both formats use
the same flat fields and units described in
[`docs/data-schema.md`](../docs/data-schema.md).

## Run on Windows PowerShell

From the repository root, use Python 3:

```powershell
py data-engine\generators\generate_synthetic_data.py
```

By default this writes 60 reproducible, one-minute readings for the `normal`
scenario with seed `42`. Choose a count, scenario, and seed as needed:

```powershell
py data-engine\generators\generate_synthetic_data.py --readings 120 --scenario warning --seed 2026
py data-engine\generators\generate_synthetic_data.py --readings 30 --scenario critical --seed 7
```

The options are:

| Option | Choices / default | Purpose |
|---|---|---|
| `--readings` | Positive integer; `60` | Number of readings to generate |
| `--scenario` | `normal`, `warning`, `critical`; `normal` | Select an illustrative value profile |
| `--seed` | Integer; `42` | Reproduce the same generated series |
| `--output-dir` | `data\synthetic` | Choose where to write both output files |

Use `--help` to display the command-line options. The generator uses only the
Python standard library.

## Example latest-reading JSON

```json
{
  "astronaut_id": "AST-001",
  "timestamp": "2026-01-01T00:59:00Z",
  "heart_rate_bpm": 76,
  "spo2_percent": 97.5,
  "body_temperature_c": 36.66,
  "respiration_rate_bpm": 15.3,
  "scenario": "normal"
}
```

The timestamp advances by one minute per record from a fixed UTC start, making
the output reproducible along with the seed. The JSON file contains the last
reading in the generated series; the CSV contains every reading.

## Tests

Run the standard-library test suite from the repository root:

```powershell
py -m unittest discover -s data-engine\tests -v
```

## Synthetic-data and safety notice

Every identifier, timestamp, and sensor value produced here is fabricated for
software demonstrations. Scenario profiles and their numeric bounds exist only
to create distinct example time series; they are not medical reference ranges,
diagnoses, operational thresholds, NASA measurements, or clinically validated
data. Do not use these readings to make health or mission decisions.
