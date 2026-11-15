import unittest
from unittest.mock import patch
import sys
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE_ROOT))
from adapters.backend_ingest import DATA_SOURCE, ingest_records, to_backend_payload


class BackendIngestAdapterTests(unittest.TestCase):
    def setUp(self):
        self.record = {
            "astronaut_id": "AST-001",
            "timestamp": "2026-01-01T00:00:00Z",
            "heart_rate_bpm": 72,
            "spo2_percent": 98.2,
            "body_temperature_c": 36.8,
            "skin_temperature_c": 32.1,
            "respiration_rate_bpm": 16.0,
            "scenario": "normal",
        }

    def test_maps_only_semantically_supported_fields_with_provenance(self):
        payload = to_backend_payload(self.record)
        self.assertEqual(payload["astronaut_id"], "AST-001")
        self.assertEqual(payload["timestamp"], self.record["timestamp"])
        self.assertEqual(payload["data_source"], DATA_SOURCE)
        self.assertTrue(payload["is_simulated"])
        self.assertEqual(payload["heart_rate"], {"value": 72, "unit": "bpm"})
        self.assertEqual(payload["spo2"], {"value": 98.2, "unit": "%"})
        self.assertEqual(payload["skin_temperature"], {"value": 32.1, "unit": "degC"})
        self.assertEqual(payload["respiration_rate"], {"value": 16.0, "unit": "breaths/min"})
        self.assertNotIn("temperature", payload)
        self.assertNotIn("body_temperature_c", payload)

    def test_body_temperature_is_never_used_as_skin_temperature(self):
        payload = to_backend_payload({
            key: value for key, value in self.record.items() if key != "skin_temperature_c"
        })
        self.assertNotIn("temperature", payload)
        self.assertNotIn("skin_temperature", payload)

    def test_rejects_boolean_and_nonfinite_measurements(self):
        for invalid in (True, float("nan"), float("inf")):
            with self.subTest(value=invalid):
                with self.assertRaises(ValueError):
                    to_backend_payload({**self.record, "heart_rate_bpm": invalid})

    def test_rejects_records_without_supported_measurements(self):
        with self.assertRaisesRegex(ValueError, "no measurements"):
            to_backend_payload({"astronaut_id": "AST-001", "timestamp": "2026-01-01T00:00:00Z"})

    def test_summary_counts_new_and_fully_reused_reading_batches(self):
        first_response = [{"id": number} for number in range(4)]
        repeated_response = [{"id": number} for number in range(4)]
        partial_retry_response = [{"id": number} for number in range(4)]
        records = [self.record, self.record | {"timestamp": "2026-01-01T00:01:00Z"}]
        with patch("adapters.backend_ingest._request_json", side_effect=[
            (200, None),  # Existing synthetic profile.
            (201, first_response),
            (200, repeated_response),
            (201, partial_retry_response),  # May contain both new and reused rows.
        ]):
            summary = ingest_records("http://localhost", records + records[:1])
        self.assertEqual(summary.batches_with_new_measurements, 2)
        self.assertEqual(summary.fully_reused_batches, 1)


if __name__ == "__main__":
    unittest.main()
