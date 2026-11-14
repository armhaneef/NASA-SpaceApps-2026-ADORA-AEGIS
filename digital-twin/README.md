# Digital twin

This module will own the interactive astronaut representation and its
visualization assets. It will consume shared data/API contracts rather than
implementing sensor or model logic itself.

**Expected inputs:** API-provided sensor summaries and clearly labeled status
or anomaly outputs.

**Expected outputs:** A visual representation that maps available data to
interface elements without implying clinical validation or certainty.

**Status:** The frontend includes a stylized/procedural renderer and loads the
local `adora-anatomy.glb` asset. The software-level mesh mappings are
documented in [`../docs/anatomical-model-integration.md`](../docs/anatomical-model-integration.md);
they are not a clinical assessment or independent scientific validation.
Member 5 owns the technical GLB integration and viewer mapping. No
individualized or clinically validated digital twin is implemented.

Scientific design boundaries and current limitations are documented in
[`scientific-methodology.md`](./scientific-methodology.md). Educational
explanations and allowed interpretations for selectable regions are in
[`../docs/anatomical-region-science.md`](../docs/anatomical-region-science.md).
These documents do not claim that the prototype is an individualized or
clinically validated digital twin.
