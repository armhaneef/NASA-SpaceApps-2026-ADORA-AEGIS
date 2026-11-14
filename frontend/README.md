# Frontend

This folder is the boundary for the user-facing web application. The frontend
will consume backend HTTP endpoints and present sensor status and prototype
outputs; it should not duplicate backend or model logic.

**Status:** Structure only; no frontend framework or interface has been
implemented.

**Expected inputs:** JSON responses from the backend API, following
[`docs/api-contracts.md`](../docs/api-contracts.md).

**Expected outputs:** User-facing views and user actions sent to documented API
endpoints. Do not present synthetic or model-generated information as verified
medical advice.
