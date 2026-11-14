"""Call Member 2's engine without implementing anomaly logic in the backend."""

import importlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator

from app.schemas.analysis import AnalysisResult
from app.services.errors import MLResponseError, MLUnavailableError


@lru_cache(maxsize=1)
def output_validator() -> Draft202012Validator:
    path = Path(__file__).resolve().parents[2] / "contracts" / "ml-analysis-output.schema.json"
    return Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))


class MLAdapter:
    """Explicit mock/local modes; never replace failed real analysis with success."""

    def analyze(self, payload: dict, input_readings: list[dict], mode: str) -> AnalysisResult:
        now = datetime.now(timezone.utc)
        common = dict(
            astronaut_id=payload["astronaut_id"], analysis_timestamp=now,
            measurement_timestamp=payload["timestamp"], data_source=payload["data_source"],
            prepared_input=deepcopy(payload), input_readings=deepcopy(input_readings),
        )
        if mode == "mock":
            return AnalysisResult(
                **common, status="mock", is_mock=True, anomaly_detected=None,
                anomaly_score=None, affected_measurements=[], model_version="backend-mock-1.0",
                explanations=["MOCK: development placeholder only. No ML model was invoked; "
                              "no health assessment, anomaly verdict, or score is available."],
                ml_result=None,
            )
        if mode != "local":
            raise ValueError("Unsupported ML adapter mode")
        try:
            analyze_health = importlib.import_module("aegis_ml").analyze_health
        except Exception as exc:
            raise MLUnavailableError(
                "Local ML module unavailable. Install optional requirements-ml.txt and "
                "configure ml-engine on PYTHONPATH, or explicitly request mode=mock."
            ) from exc
        try:
            raw = analyze_health(deepcopy(payload))
        except Exception as exc:
            raise MLUnavailableError("Local ML execution failed; no analysis was saved") from exc
        try:
            # Reject non-JSON objects/nonfinite values even inside additive fields.
            raw = json.loads(json.dumps(raw, allow_nan=False))
            output_validator().validate(raw)
            if any(raw[key] != payload[key] for key in
                   ("astronaut_id", "timestamp", "data_source")):
                raise ValueError("ML result identity does not match the input")
            anomaly = raw["anomaly"]
            expected = {"normal": False, "anomaly": True, "insufficient_data": None}
            if anomaly["is_anomaly"] is not expected[anomaly["status"]]:
                raise ValueError("Inconsistent anomaly status")
            if (anomaly["status"] == "insufficient_data") != (anomaly["normalized_score"] is None):
                raise ValueError("Inconsistent anomaly score")
            if raw["model"]["name"] != anomaly["method"]:
                raise ValueError("Inconsistent detector metadata")
        except Exception as exc:
            raise MLResponseError("Local ML returned an invalid response; no analysis was saved") from exc
        return AnalysisResult(
            **common, status=anomaly["status"], is_mock=False,
            anomaly_detected=anomaly["is_anomaly"], anomaly_score=anomaly["normalized_score"],
            # These are baseline sensor flags, NOT attribution of a joint forest result.
            affected_measurements=[key for key, value in anomaly["sensors"].items()
                                   if value["status"] == "anomaly"],
            explanations=[
                f"Overall detector: {anomaly['method']}; quality: {raw['data_quality']['status']}.",
                "Affected measurements are baseline flags, not Isolation Forest attributions. "
                "Scores are not medical probabilities. See full ml_result for quality and methods.",
            ],
            model_version=raw["model"]["version"], ml_result=raw,
        )


def get_ml_adapter() -> MLAdapter:
    """FastAPI dependency, replaceable by a test or future approved service adapter."""
    return MLAdapter()
