"""Deterministic, per-sensor historical baseline and deviation scores."""

from statistics import mean, pstdev

from .validation import SENSORS

MIN_HISTORY = 3
THRESHOLD = 3.0


def compare(values, samples):
    baseline, results = {}, {}
    for name, (_, _, _, floor) in SENSORS.items():
        history = samples[name]
        ready = len(history) >= MIN_HISTORY
        center = mean(history) if ready else None
        spread = pstdev(history) if ready else None
        scale = max(spread, floor) if ready else None
        current = values[name]["value"]
        score = abs(current - center) / scale if ready and current is not None else None
        baseline[name] = {
            "count": len(history), "mean": center, "std": spread,
            "scale": scale, "unit": SENSORS[name][0], "ready": ready,
        }
        results[name] = {
            "status": "insufficient_data" if score is None else (
                "anomaly" if score > THRESHOLD else "normal"
            ),
            "deviation_score": score,
        }
    return baseline, results
