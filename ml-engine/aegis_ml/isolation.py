"""Deterministic joint detector on complete historical sensor vectors."""

import sklearn
from sklearn.ensemble import IsolationForest

from .validation import SENSORS

MIN_ISOLATION_HISTORY = 32
RANDOM_STATE = 42
CONTAMINATION = 0.05


def detect(values, complete_history, identity_ok):
    """Return a scored result or an explicit reason to use the baseline."""
    metadata = {
        "minimum_history": MIN_ISOLATION_HISTORY,
        "training_records": len(complete_history),
        "features": list(SENSORS),
        "random_state": RANDOM_STATE,
        "n_estimators": 100,
        "contamination": CONTAMINATION,
        "sklearn_version": sklearn.__version__,
        "used": False,
        "fallback_reason": None,
        "score_threshold": None,
    }
    if not identity_ok:
        metadata["fallback_reason"] = "invalid_current_metadata"
    elif any(values[name]["value"] is None for name in SENSORS):
        metadata["fallback_reason"] = "incomplete_current_sensors"
    elif len(complete_history) < MIN_ISOLATION_HISTORY:
        metadata["fallback_reason"] = "insufficient_complete_history"
    elif len({tuple(row) for row in complete_history}) < 2:
        metadata["fallback_reason"] = "constant_history"
    else:
        forest = IsolationForest(
            n_estimators=100, max_samples="auto", contamination=CONTAMINATION,
            random_state=RANDOM_STATE, n_jobs=1,
        )
        forest.fit(complete_history)
        current = [[values[name]["value"] for name in SENSORS]]
        raw_score = float(forest.score_samples(current)[0])
        # score_samples is the negative of the original isolation anomaly score.
        # Clip only as a numerical guard; this is not a calibrated probability.
        score = min(1.0, max(0.0, -raw_score))
        metadata.update(used=True, score_threshold=float(-forest.offset_))
        return {
            "status": "anomaly" if raw_score < float(forest.offset_) else "normal",
            "normalized_score": score,
        }, metadata
    return None, metadata
