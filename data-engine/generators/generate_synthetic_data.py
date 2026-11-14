"""Generate reproducible synthetic astronaut vital-sign readings.

All values produced by this module are fabricated software-demo data. They are
not observations, medical advice, or validated clinical thresholds.
"""

import argparse
import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ASTRONAUT_ID = "AST-001"
SAMPLE_INTERVAL = timedelta(minutes=1)
START_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)
CSV_HEADERS = (
    "astronaut_id",
    "timestamp",
    "heart_rate_bpm",
    "spo2_percent",
    "body_temperature_c",
    "respiration_rate_bpm",
    "scenario",
)

# These are illustrative generator bounds, not medical reference ranges.
SCENARIOS: dict[str, dict[str, tuple[float, float, float, float]]] = {
    "normal": {
        "heart_rate_bpm": (72, 5, 55, 100),
        "spo2_percent": (98, 0.8, 95, 100),
        "body_temperature_c": (36.8, 0.16, 36.0, 37.5),
        "respiration_rate_bpm": (16, 1.5, 12, 20),
    },
    "warning": {
        "heart_rate_bpm": (104, 8, 90, 125),
        "spo2_percent": (93.5, 1, 90, 96),
        "body_temperature_c": (37.8, 0.25, 37.3, 38.5),
        "respiration_rate_bpm": (23, 2, 20, 28),
    },
    "critical": {
        "heart_rate_bpm": (138, 10, 120, 160),
        "spo2_percent": (87, 2, 80, 91),
        "body_temperature_c": (38.8, 0.4, 38.2, 40),
        "respiration_rate_bpm": (32, 3, 28, 40),
    },
}


def _bounded_value(
    rng: random.Random,
    profile: tuple[float, float, float, float],
    trend: float,
    progress: float,
    precision: int,
) -> int | float:
    """Draw a rounded value from a scenario profile and keep it in bounds."""
    average, spread, lower_bound, upper_bound = profile
    drift = trend * (progress - 0.5)
    value = rng.gauss(average + drift, spread)
    value = min(max(value, lower_bound), upper_bound)
    rounded = round(value, precision)

    if precision == 0:
        return int(rounded)
    return rounded


def generate_readings(
    number_of_readings: int = 60,
    scenario: str = "normal",
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Generate a deterministic, one-minute series for the requested scenario.

    Reusing the same number of readings, scenario, and seed produces identical
    records, including timestamps.
    """
    if number_of_readings < 1:
        raise ValueError("number_of_readings must be at least 1")
    if scenario not in SCENARIOS:
        choices = ", ".join(SCENARIOS)
        raise ValueError(f"Unknown scenario {scenario!r}. Choose from: {choices}")

    rng = random.Random(seed)
    profiles = SCENARIOS[scenario]
    readings: list[dict[str, Any]] = []

    for index in range(number_of_readings):
        progress = index / max(number_of_readings - 1, 1)
        timestamp = START_TIME + index * SAMPLE_INTERVAL
        readings.append(
            {
                "astronaut_id": ASTRONAUT_ID,
                "timestamp": timestamp.isoformat(timespec="seconds").replace(
                    "+00:00", "Z"
                ),
                "heart_rate_bpm": _bounded_value(
                    rng, profiles["heart_rate_bpm"], 3, progress, 0
                ),
                "spo2_percent": _bounded_value(
                    rng, profiles["spo2_percent"], -0.3, progress, 1
                ),
                "body_temperature_c": _bounded_value(
                    rng, profiles["body_temperature_c"], 0.08, progress, 2
                ),
                "respiration_rate_bpm": _bounded_value(
                    rng, profiles["respiration_rate_bpm"], 1.0, progress, 1
                ),
                "scenario": scenario,
            }
        )

    return readings


def write_readings(
    readings: list[dict[str, Any]],
    output_directory: Path,
) -> tuple[Path, Path]:
    """Write all readings to CSV and the newest reading to JSON."""
    if not readings:
        raise ValueError("At least one reading is required to write output files")

    output_directory.mkdir(parents=True, exist_ok=True)
    csv_path = output_directory / "astronaut_vitals.csv"
    latest_json_path = output_directory / "latest_vitals.json"

    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(readings)

    with latest_json_path.open("w", encoding="utf-8") as json_file:
        json.dump(readings[-1], json_file, indent=2)
        json_file.write("\n")

    return csv_path, latest_json_path


def _positive_integer(value: str) -> int:
    """Parse a positive integer for the command-line reading count."""
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a whole number") from error

    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate clearly labeled synthetic astronaut vital signs."
    )
    parser.add_argument(
        "--readings",
        type=_positive_integer,
        default=60,
        help="number of one-minute readings to generate (default: 60)",
    )
    parser.add_argument(
        "--scenario",
        choices=tuple(SCENARIOS),
        default="normal",
        help="demo scenario to generate (default: normal)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="random seed for reproducible output (default: 42)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "data" / "synthetic",
        help="directory for the CSV and JSON files (default: repository data/synthetic)",
    )
    return parser


def main() -> None:
    """Run the generator from the command line."""
    args = build_parser().parse_args()
    readings = generate_readings(args.readings, args.scenario, args.seed)
    csv_path, latest_json_path = write_readings(readings, args.output_dir)
    print(f"Generated {len(readings)} synthetic readings for {args.scenario!r}.")
    print(f"CSV: {csv_path}")
    print(f"Latest reading JSON: {latest_json_path}")


if __name__ == "__main__":
    main()
