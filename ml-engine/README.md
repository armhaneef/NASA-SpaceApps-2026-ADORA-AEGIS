# ML engine

This module will own model preprocessing, experiments, and evaluation. It
should consume documented sensor records and return clearly labeled prototype
outputs; it should not make clinical or mission decisions.

**Expected inputs:** Validated, unit-aware records from the data/API boundary,
plus versioned training or evaluation fixtures when these are added.

**Expected outputs:** Evaluated model artifacts and structured scores or
anomaly flags with enough context for downstream explanations.

**Status:** Structure only. No model, training data, or evaluation results are
included.
