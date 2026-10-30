# Executed verification

## Competitive upgrade and live verification — October 30

Final backend regression: **50 passed**, 0.69s, one existing upstream deprecation warning. Production frontend build and TypeScript passed; component test **1 passed**. Fixture browser suite: **10 passed in 2.0 minutes**, covering desktop/mobile group evidence, retained preferences, revisions, original planning, constraints, keyboard entry, photo credits, reduced motion and API errors. Inspected the group mobile screenshot.

Live Qloo smoke: **3 calls passed** (exact search, 20 Chicago places, five-ID scoped rescore). It revealed and fixed a real schema mismatch: search returns `types`, not necessarily `subtype`; two regression tests added. Full live desktop browser: **passed**, six calls, 20 candidates, two profiles, three provisional group choices. Zero confirmed stops and budget incomplete are expected because practical venue facts remain unknown. Only safe aggregate status is saved under evaluation/results; no raw live response corpus. Root .env is ignored.

Standalone Next startup now uses `frontend/scripts/start.cjs` to copy static/public assets and run the generated server. Local startup verified. Docker engine is unavailable; combined image remains unbuilt. Remote CI, public deployment, live LLM baseline and human quality evaluation remain unverified. Earlier sections below are historical, not current test counts.

## Frontend redesign regression

The consumer redesign passed the production build, 35 backend tests (1.90s), one component test (2.77s runner duration), and eight desktop/mobile Playwright checks (31.5s). Additional checks cover photography loading, profile edits, dietary/access controls, keyboard skip navigation, image credits, and reduced motion. See FRONTEND_REDESIGN.md for the design changes and verification scope. Existing backend behavior remains unchanged.

## Initial implementation

Local session 2026-10-28, America/New_York. No live provider credentials were used.

| Check | Actual result |
|---|---|
| `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest backend/tests -q` | **35 passed**, 1.88s final run |
| `npm test` in frontend | **1 passed**, 14.98s |
| `npm run build` | **Succeeded**, Next.js 16.4.3 compilation, TypeScript and static page generation |
| `npm run test:e2e` | **4 passed**, 9.7s final run; desktop Chrome and mobile Chromium |
| `python -m evaluation.run` | **15 fixture scenarios completed**, raw and aggregate JSON saved |
| Desktop/mobile screenshot inspection | Completed; form, labels and layout visible; no horizontal viewport overflow in tests |
| `git check-ignore .env` | Confirmed ignored |
| `npm audit --omit=dev --json` | **0 reported production dependency vulnerabilities** |

Backend coverage: request construction, response parsing, exact/ambiguous/missing entities, malformed responses, auth rejection, retry/timeout limits, safe origins, aggregate budget, unknown facts, hard constraints, typed stream transitions, revisions, fixture provenance, live-path provisional facts with mock HTTP, validated interpreter outputs with mock HTTP.

Browser coverage: landing page, favorite entry, frontend/backend streaming integration, result rendering, ranking comparison, stop replacement, cheaper revision, strict-hours rejection, API failure and usable retry button. Tests ran against the production frontend and actual local FastAPI server, with fixture data. The API-error case intentionally intercepts the request.

Initial browser run: 2 passed and 2 failed because `getByRole('alert')` also matched Next.js's route announcer. Scoped the locator to the expected app error; rerun passed all four. Initial restricted Python commands stalled; successful runs used the approved local runner.

Warning: installed Starlette warns that its HTTPX TestClient integration is deprecated in favor of httpx2. This did not fail tests; migration is deferred.

Not run: live Qloo requests, live OpenAI requests, hosted end-to-end checks, Docker image build, LLM-only baseline, blinded human study, exhaustive accessibility/security audit. No public deployment or source publication occurred. Dependencies are pinned/locked, but this is not a security certification.

Live mobile follow-up (October 30): standalone Next server startup and the full two-profile browser workflow passed; six Qloo calls, 20 candidates, three provisional choices, no horizontal overflow, zero confirmed stops and budget incomplete. Safe status: evaluation/results/live_browser_mobile_status.json. No raw response corpus saved.

OpenAI live verification (October 30): gpt-4.1-mini passed two requests through the running Next/FastAPI endpoint: $75/person remained 75; $90 total for three became 30/person. All other fields, including companion constraints and inherited budgets, were preserved. Initial probes revealed budget-unit and companion-preservation errors; extraction instructions were corrected before the passing rerun. This verifies tested intent extraction cases, not general accuracy or an LLM-only recommendation baseline. Evidence: evaluation/results/live_openai_status.json.
