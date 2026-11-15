# AEGIS full-system integration QA — 2026-11-15

## Current checkpoint and scope

The integration HEAD before this correction pass is
`37e2dddd6af62c9d08696e32939a7f1e8ae1942a` (`37e2ddd`), on
`feature/aegis-final-full-integration`. The pass began with a clean working tree.
The committed anatomy/astronaut-marker implementation is retained. This later
security/documentation correction remains uncommitted for independent Copilot
review; no commit, push, merge, PR creation or PR #15 change is authorized here.

**Real full browser-to-Gemini generation: NOT VERIFIED.** Documentation and
mock/stub integration evidence do not close that acceptance gate. Resolve any
independent review findings, obtain separate approval for live acceptance if
required, and obtain publication approval before GitHub delivery.

## Evidence ledger: earlier verification versus this pass

The pre-correction results below were independently executed in earlier review/
QA turns against `37e2ddd` (or the identical pre-commit anatomy implementation).
They are not silently presented as fresh executions during this correction.

| Check | Earlier independently verified result | Personally rerun during this correction pass |
|---|---|---|
| Data engine | 15 tests + 9 subtests, 0 failed/skipped | Not rerun; implementation unchanged |
| Backend | 180 passed, 0 failed/skipped | **180 passed**, 0 failed/skipped |
| ML engine | 77 passed, 0 failed/skipped | Standalone suite not rerun; real ML also exercised by backend/workflow tests |
| AI Assistant | 69 passed, 0 failed/skipped | **113 passed**, 0 failed/skipped: original 69 + 44 CORS regressions |
| Frontend unit/contract/anatomy tests | 46 passed, 0 failed/skipped | **46 passed**, 0 failed/skipped |
| Existing anatomy browser checks | 30 passed (25 + 5) | Not rerun; frontend/model unchanged |
| New drawer/astronaut browser regressions | 23 passed in one clean execution, 0 failed/skipped | Not rerun; frontend/model unchanged |
| Additional disposable integration workflow | 15 checks passed | **15 checks passed**, 0 failed; stub LLM only |
| Frontend lint and production build | Passed; existing bundle warning | Not rerun; frontend/package files unchanged |

The earlier main-suite total is 387 tests plus 9 data subtests; it excludes
browser checks and the additional 15 workflow checks. It is a prior checkpoint
aggregate, not a claim that every suite was rerun after this correction. The
older 375-test/34-frontend and 27-browser figures are retained only in the
explicit historical record below; do not add overlapping historical browser
counts to the current 30 + 23 evidence groups.

The initial new CORS test execution found acceptance of empty user-info syntax
(`http://@localhost`). Original URL components are now checked as well as
normalized URLs; the complete AI suite was rerun and passed all 113 tests.
This was a development finding, not a waived test failure.

Python tests used existing isolated environments (backend pytest 9.2.0 and
AI pytest 8.4.2). An external QA launcher suppressed private dotenv loading,
removed provider credentials from the test process, blocked external/live
provider connections, and allowed disposable loopback HTTP fixtures. The AI
suite's temporary dotenv fixture remained permitted. No private `.env` file
was read, printed or modified; no Gemini/live chat request was made.

The 15-check workflow used 40 generated records, a temporary SQLite database,
real Isolation Forest trained on 39 earlier records, persisted/retrieved
analysis, and the actual backend HTTP bridge to a disposable AI app with a
stub LLM. It checked explicit mock bypass, minimal context, unknown analysis,
policy refusal, provider failure and service outage. Stub replies deliberately
exercise non-mock-labelled response contracts; they are not real generation.
Backend/AI contract suites cover malformed responses, identity mismatches,
502/503/504 behavior, provenance and sanitized errors.

## Current security corrections

AI CORS keeps explicit development defaults when `AI_ALLOWED_ORIGINS` is
omitted. A configured list must contain valid explicit HTTP(S) origins;
wildcards, empty entries, credentials, paths, queries and fragments fail at
startup. Credentialed CORS is disabled because these JSON routes do not use
cookie/session authentication. Regression tests check allowed responses,
unauthorized preflight rejection and invalid-configuration import failure.
Backend CORS and provider configuration behavior are unchanged.

Repository ignore rules now include SQLite journal/WAL/SHM sidecars and a
root-anchored `/.integration/` rule. **24 safe path probes passed**, including
source/docs/example-template visibility. The integration match comes from the
tracked `.gitignore`, not just a machine-local Git exclude. Existing local
exclude settings and worktrees were not changed.

Documentation checks passed for 32 local links/anchors in the six changed
Markdown files. All 11 documented AI routes match the source; frontend scripts,
environment names and explicit Vite flags were checked against local code/CLI.
`git diff --check` passed, as did final-newline/trailing-whitespace checks on
all 10 changed/new files. The changed-file security scan detected no credential
patterns or private environment-file changes. These are local checks, not a
fresh vulnerability-database audit.

## Live acceptance ledger and limits

- **Two previous integration live acceptance attempts returned HTTP 503**, as
  reported for this checkout. This pass did not repeat them and does not infer
  a provider/credential/billing cause from the status alone. They are distinct
  from intentionally mocked 503 tests.
- Previous read-only checks returned HTTP 200 for backend `/health` on 8000
  and AI `/api/v1/health` on 8002; the latter reported `configured`. These are
  service/configuration observations, not proof of a valid key or generation.
- Earlier Member 3 reports describe component-level Gemini chat successes in
  another verification context. They do not prove the current complete
  `React -> :8000/ai/assistant -> :8002/api/v1/assistant/respond -> Gemini -> UI`
  path. Retain them as historical evidence, not current acceptance.
- Missing analysis remains unknown. Explicit mock/offline text, controlled
  stubs, safety refusals and non-mock flags alone do not prove real Gemini.
  A separately approved live acceptance must observe the complete path,
  matching astronaut, actual provider configuration, nonempty answer and
  limitations, provenance and browser rendering. No key belongs in a report.

## Non-blocking limitations

All data is fabricated educational input, not NASA astronaut telemetry, and
neither ML nor anatomy is medically/clinically validated. Global findings are
not localized. See [anatomy geometry and marker limits](anatomy-layer-improvements.md):
128 meshes include 34 organ-group meshes, not 34 distinct organs; face/scalp
muscles, segmented regional skin and a standalone abdomen mesh are absent.

Physical mobile-device performance is not benchmarked. The model has over a
million triangles; the existing frontend bundle warning remains (about 1.66 MB
minified / 466 kB gzip). Previous Chrome/SwiftShader checks are not hardware
benchmarks. Backend tests retain the Starlette TestClient/httpx deprecation;
AI tests additionally retain SpeechRecognition's `aifc` deprecation. These are
warnings, not failures. Hardware microphone capture/audible speech remains
unverified. Local-only dependency checks do not constitute fresh CVE clearance.

## Historical integration record: 743aa11, before anatomy and later acceptance attempts

The following original report is preserved as historical evidence. Its
34-frontend/375-total, 27-browser, offline-health and no-attempt statements refer
to that earlier checkpoint, not the current record above. Statements about
unchanged Member 3 files and pending wiring describe that phase's scope.

### Delivery checkpoint

**BLOCKED: real Gemini acceptance and GitHub delivery.** The Team Lead is
configuring Gemini privately. No cloud generation was requested during this
integration. A separate, explicit approval is required after configuration,
before exactly one synthetic educational question is submitted through the UI.
The feature branch remains local until that acceptance gate is satisfied.
No PR was created; neither `dev`, `main`, nor PR #15 was merged or modified.

### Source preservation and ancestry

- Integration branch: `feature/aegis-final-full-integration`.
- Isolated checkout: `.integration/full-system` under the original workspace.
- Latest fetched `origin/dev`: `6e01b2d3973290ad2629cdf49eaf39489d5f685a`;
  a second fetch after QA confirmed the same head.
- Codex work preserved in `d56d4e8` on `feature/ui-ux-completion`; includes
  the complete history through `0b541dc` and `f118847`, rather than one picked
  UI commit. The original worktree's unrelated untracked file is preserved.
- Copilot's six files preserved in `6b43fff` on
  `feature/gemini-dashboard-integration`. Its worktree was not switched.
- Both branches are combined with merge ancestry. Source patches are retained
  outside the tracked checkout in `.integration/`.
- All Member 3 files match latest `origin/dev`; Gemini provider, configuration,
  FastAPI endpoints, tests, SDK requirements, safety, local NASA retrieval and
  voice prototype are included unchanged. Section 14 of the Member 3 readiness
  report supersedes its historical port-8001/OpenAI-only sections.
- PR #15 remains open. Its head `0b541dc398f4c17069b63f8ed8a34cf91eb9b74e`
  is an ancestor of the integrated UI history; no missing functionality was
  found by ancestry/content comparison. It was not merged or closed on GitHub.
- No private `.env` or credentials were copied. Existing environments,
  databases and the original Vite service on port 5175 are preserved.

See [the complete changed-file manifest](aegis-final-integration-files.txt)
for all files changed relative to the integrated dev head, including inherited
UI/data/backend work.

### Backend and frontend integration

**COMPLETE AND VERIFIED** with fake HTTP/provider transports and offline
running services:

`React -> POST :8000/ai/assistant -> Member 4 adapter -> POST :8002/api/v1/assistant/respond`.

The bridge defaults to the full `AI_ASSISTANT_URL` endpoint on port 8002,
supports the earlier base-URL setting, and permits explicit blank configuration
to disable it. HTTP uses a maximum five-second connection timeout and a
70-second response timeout. Assistant requests in React allow 90 seconds,
above Member 3's documented 60-second model timeout. Production requirements
now include `httpx`.

Only validated astronaut/question/selected-summary fields are forwarded.
Redirects and ambient proxies are disabled. No provider key is sent by the
backend or browser. Mock mode never calls HTTP. Unavailable/network failures
produce safe 503 errors; transport/upstream timeout gives 504; malformed JSON,
empty/malformed schema and wrong astronaut identity give 502. No private
prompt, key or raw provider body is logged by the bridge.

Copilot's form, transcript, loading/error states and duplicate guard are
retained. Context changes cancel requests and discard stale replies. Replies
show mock/non-mock labels, version, status, data source, analysis context and
limitations. Non-mock status alone never claims Gemini identity. Automatic
dashboard explanations always request mock mode, so opening a page, changing
astronaut or running ML cannot spend a model request. Only explicit chat
submission uses configured local mode. Missing analysis remains unknown.

Backend changes require **Member 4 review**. Member 3's schema is unchanged;
Member 3 should confirm the configured provider/model and timeout for live
acceptance. Any future provider-identity schema extension needs coordination.

### Automated test results

| Suite | Result | Notes |
|---|---:|---|
| Data engine | 15 passed + 9 subtests | Generation, serialization, CLI, ingest mapping |
| Backend | 180 passed | SQLite, ingestion, ML HTTP persistence, assistant bridge and failures |
| ML engine | 77 passed | Personalized baseline, Isolation Forest, trends and contracts |
| AI Assistant | 69 passed | Also verified using declared pytest 8.4.2; no cloud calls |
| Frontend | 34 passed | API, timeouts, provenance, identity, scenarios and localization |
| Frontend lint | Passed | `npm.cmd run lint` |
| Production build | Passed | `npm.cmd run build` |
| Whitespace | Passed | `git diff --check` |

Total: **375 main tests plus 9 subtests**, all passing. Backend produced one
Starlette/httpx deprecation warning. AI Assistant produced that warning plus a
SpeechRecognition `aifc` deprecation warning. Build reports a large bundle
(about 1.66 MB minified / 463 kB gzip); this remains a performance warning.

Initial sandbox runs failed on pytest/Python temporary-directory permissions
and Node child-process spawning. Final Python suites ran with approved access
and fresh isolated test directories; no tests were skipped or patched to hide
failures. Frontend tests used Node's `--test-isolation=none` to avoid forbidden
child-process spawning. The AI suite also passed with isolated pytest 8.4.2,
within its requirements range. Shared package environments were preserved;
SDK/QA tooling was installed separately under ignored `.integration/`.

### Running-service and browser evidence

**COMPLETE AND VERIFIED:** synthetic generation -> backend HTTP ingestion ->
separate SQLite QA database -> local ML analysis -> saved non-mock algorithmic
result -> dashboard metrics/history. Repeating the 60-batch seed reused all
60 batches with no new measurements. A real saved analysis reports
`is_mock:false`, `status:normal`, model version `2.0.0`; this is ML on synthetic
inputs, not Gemini and not clinical validation.

Chrome browser checks: **27 passed**, desktop 1440x1000 and mobile 390x844.
Checks cover all ten demo scenarios, actual Three.js material colors, global
alerts remaining unlocalized, matching alert-card/mesh selection, rotation,
zoom/reset, layers/wire mode, baseline clearing, live API readings/charts,
offline provider 503, chat loading/duplicate prevention, fixture-labelled
non-mock and mock replies, network/504 errors, stale-response cancellation,
mobile overflow, drawer selection/focus, and JavaScript exceptions.

The non-mock chat success in these checks is an explicit **browser fixture**,
not a genuine provider result. Expected 404 (absent analysis), 503, 504 and
network errors were exercised; there were no uncaught browser JavaScript
exceptions. Browser QA was resumed after correcting harness selectors/waits;
only unique passing checks are counted. Additional screenshot review identified
and fixed delayed mobile drawer text under reduced motion: inherited visibility
was transitioning through descendants because every element had a nonzero
transition duration. Reduced-motion transitions now use zero duration. Final
computed styles and screenshots confirm visible region and chat controls;
desktop/mobile visual review is complete.

QA artifacts, screenshots, logs and harnesses are local under
`.integration/qa-results/` and `.integration/`; they are not production assets.
QA services use ports 8000, 8002 and 5176, with an isolated database. The
existing service on 5175 was preserved.

NASA local search returned five results with `evidence_available:true` over
real HTTP. The voice demo route returned 200; voice status reports microphone
unavailable and speech-output capability present. Hardware microphone capture
and actual audible speech output are **IMPLEMENTED BUT NOT VERIFIED** here.
Voice route/service tests use controlled fixtures.

### Real Gemini acceptance and remaining gate

**IMPLEMENTED BUT NOT VERIFIED:** the final `Member 3 -> Gemini -> UI` leg.
Health on port 8002 currently reports `offline`, `llm_available:false`, seven
knowledge documents. Health is configuration evidence only. The official
Gemini/OpenAI SDKs were installed into isolated tooling after one DNS/download
failure and a successful bounded retry. No key was entered by the integration
agent, and no generation was attempted.

After the Team Lead confirms private setup, restart only the integration-owned
AI service with that private configuration, check configuration/health, then
request separate approval for one safe synthetic question. Verify the whole UI
path, correct astronaut, nonempty answer/limitations, `is_mock:false`, actual
Gemini configuration and browser rendering. Do not infer success from mocked
tests or an available health endpoint. If this cannot be completed, retain
**BLOCKED** and do not perform the final push/PR delivery.

Once acceptance is complete, recheck staged files for secrets, commit the
acceptance record, push only the new feature branch and open a PR targeting
`dev`. Never force-push, merge automatically, or modify/close PR #15.
