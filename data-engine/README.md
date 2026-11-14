# Data engine

This module will own generation of explicitly synthetic fixtures and reusable
sensor-data preprocessing. It is separate from the API, ML, and visualization
modules so each can evolve independently against the shared schema.

**Expected inputs:** Synthetic source parameters or JSON readings conforming to
[`docs/data-schema.md`](../docs/data-schema.md).

**Expected outputs:** Reproducible synthetic JSON fixtures and/or validated,
preprocessed records with units and provenance preserved.

**Status:** Structure only. No generator or preprocessing code exists yet.
Never label generated examples as NASA measurements or real astronaut data.
