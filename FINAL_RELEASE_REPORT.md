# Final release handoff â€” October 30, 2026

## Decision

**Ready for owner-operated Heroku deployment; NO-GO for submission until the public application is verified.** Owner explicitly requested source publication and will deploy personally. No Heroku app, dyno, add-on or secret configuration was created by the agent.

## Changes

- Protected baseline in ignored `.research/release-baseline/` with SHA-256 manifest.
- `backend/app/safety.py`, `main.py`: body limits, process-wide route limits and interpreter concurrency.
- `frontend/lib/example.ts`, `GroupReport.tsx`, `page.tsx`: editable four-person example, per-person fair/mean tradeoff table, same-choice disclosure and explicit provider data-sharing notices.
- `Dockerfile`, `heroku.yml`, `app.json`, `scripts/serve.py`: one non-root container, internal-only backend, host-assigned public port and Heroku browser/remote-build handoff.
- `.github/workflows/ci.yml`: Python, frontend, fixture evaluation, browser and container smoke checks.
- `scripts/judge_smoke.cjs`: repeatable real UI rehearsal, constraint rejection, invalid input, mobile layout and authentic screenshots.
- `docs/`: architecture diagram, deployment steps, two-minute script, finalist outline, judge questions, fairness methodology and final checklist.

## Verification

Local final checks: **53 backend tests**, **12 desktop/mobile browser tests (49.1s)**, **one component test**, production build/TypeScript, `pip check`, zero reported production npm vulnerabilities. One existing Starlette/httpx deprecation warning. Initial build lock was resolved by stopping the app server before rebuilding.

Live four-profile rehearsal: **nine Qloo calls, 20 candidates, one provisional choice**. Both objectives selected the same place; no live fairness uplift is claimed. Added access requirement rejected unknown facts; invalid negative budget returned 422. Two prior live OpenAI budget edits passed with all unrelated fields retained. No live quality benchmark or LLM-only recommender comparison was run; deployment was prioritized as requested.

Source files were checked for both configured secrets before publication. `.env` is ignored. No raw live Qloo corpus is published; screenshots and aggregate status are included. Five actual screenshots are in `docs/screenshots/`.

## Qloo and agentic behavior

Real capabilities: `/search` resolves artist/movie/book/brand names to IDs; `/v2/insights` discovers geographically scoped places and rescores a shared ID pool per person using `filter.results.entities`; one conditional extra page is available. Ordered returned results supply a relative proxy, not a fabricated Qloo satisfaction score.

The controlled workflow makes meaningful tool decisions: resolve, discover, reject unknown hard requirements, expand once if needed, obtain per-person evidence, optimize bounded subsets, verify invariants, replan from feedback. OpenAI edits typed intent; it is not claimed to be an autonomous planner. Max-min is exact only within the bounded candidate pool and declared objective.

## Real versus simulated

Live mode uses actual Qloo and optional OpenAI. Fixture mode uses six fictional Chicago venues and an authored preference matrix, always labeled; it is never an automatic live-error fallback. Costs and practical venue facts are not independently verified. Provisional discoveries are not confirmed itineraries or bookings. Synthetic objective differences are documented in `docs/FAIRNESS_DEMO.md`.

## URLs and remaining gates

- Public source: https://github.com/leninathikam/tastepilot-ai â€” PUBLIC, MIT recognized.
- Implementation commit: `7e4df3ead8e721b6db58295af40bbbe9d4ae4d13`.
- CI: https://github.com/leninathikam/tastepilot-ai/actions/runs/41081525719 â€” **SUCCESS**; remote Linux container build/startup, backend, frontend and browser checks passed.
- Heroku setup form (not a demo URL): https://heroku.com/deploy?template=https://github.com/leninathikam/tastepilot-ai
- Public app URL: **not yet deployed/verified**. Owner must supply the resulting URL.

Main risks: hosted build/availability until checked; unknown venue practicality; proxy validity; single-process limits reset on restart and are not billing caps; broad input/entity cases remain untested live. Keep judge access working through November 5, 11:45 p.m. Eastern. No first-place guarantee, proven human fairness, measured satisfaction or commercial traction is supported.

Documentation-only follow-up commits do not change the tested implementation. Heroku itself is still unverified; a passing Docker smoke is not proof of the deployed public application.
