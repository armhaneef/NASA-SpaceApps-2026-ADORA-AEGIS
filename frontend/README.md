# AEGIS frontend

React/Vite dashboard with synthetic metrics and charts, DEMO/LIVE API modes,
an assistant chat UI, and a Three.js anatomical viewer. Included readings are
fabricated educational data, not NASA telemetry or clinical measurements.

## Run on Windows

From the repository root, using Node.js/npm compatible with the locked Vite
(its local package declares Node `^20.19.0 || >=22.12.0`):

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run dev
```

Open the URL printed by Vite. `vite.config.js` enables React and does not pin a
host or port. Vite normally starts at 5173 and can select a later port when
occupied; do not assume it matches a backend allowlist.

For the root README's integrated demo, explicitly select an available port:

```powershell
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
$env:VITE_API_TIMEOUT_MS = '10000'
$env:VITE_ASSISTANT_MODE = 'mock'
npm.cmd run dev -- --host localhost --port 5175 --strictPort
```

`--strictPort` fails if 5175 is occupied. For another port, change that argument
and configure backend `AEGIS_CORS_ORIGINS` to include the exact browser origin.
The backend defaults allow `http://localhost:5173` and `http://localhost:5175`.
See the [integrated setup](../README.md#run-the-integrated-synthetic-demonstration-on-windows)
for backend/ML startup, a temporary SQLite database and synthetic seeding.

## Modes and anatomy

DEMO MODE needs no backend. All ten scenarios are synthetic: global vital
alerts remain global, while explicit localized warning/critical markers are
yellow/red. Missing regional sensors remain NO DATA; cyan is only an unmarked
demo reference. Custom markers belong to the selected astronaut for the current
session. Switching astronauts restores that astronaut's markers; scenario
changes clear that astronaut's custom overlay. Layers and camera reset preserve
markers.

FULL BODY, SKELETON, MUSCLES and ORGANS retain the existing 128-mesh model,
including 34 organ-group meshes. MUSCLES retains a transparent head reference
because dedicated facial/scalp muscles are absent. Read the
[asset and geometry limits](../docs/anatomy-layer-improvements.md).

LIVE API MODE calls the central backend on port 8000 for synthetic profiles,
readings, charts and saved ML analyses. ML execution requires the optional
backend ML dependencies and `ml-engine` on `PYTHONPATH`.

The assistant calls only `POST /ai/assistant` on the backend. Mock mode is the
default and invokes no provider. `VITE_ASSISTANT_MODE=local` enables explicit
user questions through the backend-to-AI bridge on port 8002. Only use it for
real generation after separate approval. Automatic explanations remain mock.
Fixture/stub successes and `is_mock:false` alone do not establish Gemini
provenance; see [assistant setup and response labels](../docs/gemini-dashboard-chat.md).
Never put Gemini/OpenAI keys in frontend code or any `VITE_*` setting.

## Scripts and tests

Run from `frontend`:

```powershell
npm.cmd run lint
npm.cmd run build
npm.cmd run preview
node --test --test-isolation=none tests/*.test.js
```

These are the actual package scripts; there is no `npm test` script. Preview
serves a production build and prints its own URL. The large-bundle warning is
known; physical mobile-device performance has not been benchmarked.

The separate browser regression suite requires installed Chrome and Playwright
plus a running frontend. From the repository root:

```powershell
$env:AEGIS_BROWSER_TEST_URL = 'http://localhost:5175/'
node --test frontend/tests/reviewFindings.browser.mjs
```

The harness resolves installed `playwright/test` or integration QA tooling;
`AEGIS_PLAYWRIGHT_MODULE` can provide an absolute module path. Its fallback URL
is 5176, so set the URL to the actual server. It blocks provider/chat requests
and does not verify Gemini. See [dated QA evidence](../docs/aegis-final-integration-qa.md)
for executed counts and limitations. No output is a diagnosis or medical/mission
recommendation.
