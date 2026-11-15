"""Tests for the standard-library synthetic vital-sign generator."""

import csv
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


GENERATOR_DIRECTORY = Path(__file__).resolve().parents[1] / "generators"
sys.path.insert(0, str(GENERATOR_DIRECTORY))

from generate_synthetic_data import (  # noqa: E402
    ASTRONAUT_ID,
    CSV_HEADERS,
    SCENARIOS,
    generate_readings,
    main,
    write_readings,
)


EXPECTED_FIELDS = {
    "astronaut_id",
    "timestamp",
    "heart_rate_bpm",
    "spo2_percent",
    "body_temperature_c",
    "skin_temperature_c",
    "respiration_rate_bpm",
    "scenario",
}


class SyntheticDataGeneratorTests(unittest.TestCase):
    def test_records_have_the_shared_flat_schema(self) -> None:
        readings = generate_readings(number_of_readings=3)

        self.assertEqual(len(readings), 3)
        for reading in readings:
            self.assertEqual(set(reading), EXPECTED_FIELDS)
            self.assertEqual(reading["astronaut_id"], ASTRONAUT_ID)
            self.assertEqual(reading["scenario"], "normal")
            self.assertTrue(reading["timestamp"].endswith("Z"))

    def test_timestamps_advance_in_one_minute_steps(self) -> None:
        readings = generate_readings(number_of_readings=3)

        self.assertEqual(
            [reading["timestamp"] for reading in readings],
            [
                "2026-01-01T00:00:00Z",
                "2026-01-01T00:01:00Z",
                "2026-01-01T00:02:00Z",
            ],
        )

    def test_generation_is_reproducible_for_each_scenario(self) -> None:
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                first = generate_readings(12, scenario=scenario, seed=2026)
                second = generate_readings(12, scenario=scenario, seed=2026)
                self.assertEqual(first, second)

    def test_skin_temperature_is_separate_bounded_and_scenario_independent(self) -> None:
        series = {
            scenario: generate_readings(20, scenario=scenario, seed=91)
            for scenario in SCENARIOS
        }
        expected_skin = [row["skin_temperature_c"] for row in series["normal"]]
        self.assertEqual(
            [row["skin_temperature_c"] for row in series["warning"]], expected_skin
        )
        self.assertEqual(
            [row["skin_temperature_c"] for row in series["critical"]], expected_skin
        )
        for value in expected_skin:
            self.assertGreaterEqual(value, 30.3)
            self.assertLessEqual(value, 33.3)
        self.assertNotEqual(
            [row["body_temperature_c"] for row in series["normal"]], expected_skin
        )

    def test_generator_accepts_explicit_synthetic_astronaut_id(self) -> None:
        readings = generate_readings(2, astronaut_id="AST-DEMO-02")
        self.assertEqual({row["astronaut_id"] for row in readings}, {"AST-DEMO-02"})
        with self.assertRaisesRegex(ValueError, "astronaut_id"):
            generate_readings(1, astronaut_id=" ")

    def test_values_stay_within_the_selected_demo_scenario_bounds(self) -> None:
        for scenario, profiles in SCENARIOS.items():
            with self.subTest(scenario=scenario):
                readings = generate_readings(100, scenario=scenario, seed=11)
                for reading in readings:
                    for field_name, (_, _, lower, upper) in profiles.items():
                        self.assertGreaterEqual(reading[field_name], lower)
                        self.assertLessEqual(reading[field_name], upper)

    def test_writes_csv_and_latest_json(self) -> None:
        readings = generate_readings(5, scenario="warning", seed=7)

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "synthetic"
            csv_path, json_path = write_readings(readings, output_directory)

            with csv_path.open(newline="", encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                csv_rows = list(reader)

            latest_json = json.loads(json_path.read_text(encoding="utf-8"))

            self.assertEqual(tuple(reader.fieldnames or ()), CSV_HEADERS)
            self.assertEqual(len(csv_rows), len(readings))
            self.assertEqual(latest_json, readings[-1])
            self.assertEqual(latest_json["scenario"], "warning")

    def test_command_line_options_generate_requested_scenario_and_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "generated"
            arguments = [
                "generate_synthetic_data.py",
                "--readings",
                "4",
                "--scenario",
                "critical",
                "--seed",
                "2026",
                "--output-dir",
                str(output_directory),
            ]

            with patch.object(sys, "argv", arguments), redirect_stdout(io.StringIO()):
                main()

            with (output_directory / "astronaut_vitals.csv").open(
                newline="", encoding="utf-8"
            ) as csv_file:
                rows = list(csv.DictReader(csv_file))
            latest_json = json.loads(
                (output_directory / "latest_vitals.json").read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(len(rows), 4)
            self.assertEqual(latest_json["scenario"], "critical")
            self.assertEqual(latest_json["astronaut_id"], ASTRONAUT_ID)

    def test_rejects_non_positive_reading_count(self) -> None:
        with self.assertRaises(ValueError):
            generate_readings(0)

    def test_rejects_unknown_scenario(self) -> None:
        with self.assertRaises(ValueError):
            generate_readings(1, scenario="unknown")


if __name__ == "__main__":
    unittest.main()
