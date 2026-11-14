"""Descriptive historical trends; no forecasts or medical interpretation."""

from statistics import mean

from .validation import SENSORS

MIN_TREND_HISTORY = 3


def analyze_trends(timed_samples):
    results = {}
    for name, points in timed_samples.items():
        points = sorted(points, key=lambda point: point[0])
        floor = SENSORS[name][3]
        result = {
            "direction": "unknown", "count": len(points),
            "slope_per_hour": None, "unit": SENSORS[name][0] + "/hour",
            "fitted_change": None, "change_threshold": floor,
            "start_timestamp": points[0][0].isoformat() if points else None,
            "end_timestamp": points[-1][0].isoformat() if points else None,
        }
        if len(points) >= MIN_TREND_HISTORY:
            span = (points[-1][0] - points[0][0]).total_seconds()
            if span > 0:
                # Normalize time to the observed span for numerical stability.
                xs = [(time - points[0][0]).total_seconds() / span for time, _ in points]
                ys = [value for _, value in points]
                x_mean, y_mean = mean(xs), mean(ys)
                change = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / sum(
                    (x - x_mean) ** 2 for x in xs
                )
                direction = "stable" if abs(change) <= floor else (
                    "increasing" if change > 0 else "decreasing"
                )
                result.update(direction=direction, slope_per_hour=change * 3600 / span,
                              fitted_change=change)
        results[name] = result
    return results
