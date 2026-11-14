# Digital Twin API proposal — draft for Member 6

**Not an implemented endpoint or an approved shared contract.** Inspection found
no Twin router, schema or service in the backend. The sibling Digital Twin module
is currently a documented placeholder. Existing `/health/.../latest`, `/history`
and `/analyses/...` routes can supply raw integration data in the meantime.

Proposed future route: `GET /twin/{astronaut_id}/analysis` (the name from the
original backend plan). This would be a read-only aggregation of stored readings
and selected saved ML output, never a request that triggers new inference.

One possible response when a reading exists but analysis/alerts are unavailable:

```json
{
  "astronaut_id": "AST-UI-001",
  "snapshot_timestamp": "2026-11-14T10:05:00Z",
  "indicators": [
    {
      "measurement_type": "heart_rate",
      "latest": {
        "reading_id": 1,
        "value": 78,
        "unit": "bpm",
        "timestamp": "2026-11-14T10:00:00Z",
        "sensor_type": "smart_band",
        "source": "synthetic_example",
        "is_simulated": true,
        "quality": "simulated"
      },
      "baseline": null,
      "anomaly": null
    }
  ],
  "analysis": null,
  "alerts": {"availability": "not_implemented", "items": null}
}
```

If analysis exists, its proposed summary would reference the saved analysis ID,
generation and measurement timestamps, `is_mock`, status, source, model version,
data quality, overall detector method and sensor method. Baseline fields would
come directly from Member 2's saved baseline output (count, unit, readiness, mean,
standard deviation and scale); anomaly fields would preserve its nullable status
and scores. No independent thresholds, predictions or medical interpretation
would be added. Any baseline comparison must use matching units and identify
the exact analysed reading, not assume the newest reading was analysed.

## Decisions required before implementation

1. Confirm route name, requested indicators and response shape with Member 6.
2. Decide whether indicators reflect latest available readings or one coherent
   saved analysis snapshot. Their timestamps may differ; define treatment of
   newer unanalysed readings, multiple sources, and source selection.
3. Agree on units and semantic mappings. ML heart-rate baselines use `beats/min`,
   while storage may use `bpm`; ML `temperature` means skin, while storage also
   permits a legacy ambiguous `temperature`. Preserve those distinctions.
4. Define missing, stale, mock and insufficient-data display behavior. Timestamp
   information is available; freshness thresholds have not been agreed.
5. Confirm analysis selection: latest saved result may be a mock. Decide whether
   the caller selects an ID or whether filtering real results is required.
6. Define alert availability/status together with the approved alert workflow.
   There is no alert table/API yet. `null`/unavailable must not be represented as
   a reassuring empty list meaning no alerts.
7. Agree on baseline readiness and representation of unavailable comparisons.
   Do not calculate new anomaly logic from the baseline in the backend.
8. Confirm empty-data behavior (proposed empty indicators and null analysis) and
   unknown-astronaut behavior (proposed 404), plus polling needs.

Body-region mapping, colors, animation, and Three.js implementation remain
Member 6's responsibility. This document does not assign visual states or modify
shared documentation. Implement and test the endpoint only after agreement.
