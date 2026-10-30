# Release findings â€” October 30, 2026

## Baseline protection and verification

Before edits, preserved all 76 publishable files in ignored `.research/release-baseline/before-release-hardening.zip`, with per-file SHA-256 manifest. Archive SHA-256: `8f9422795eac1b3a3c8d9b6e3a68dd01ae79d946da71e40fa0138835d2680af2`. Both configured secrets were scanned out of publishable files. Git has no commits or remote; no history can contain credentials yet. Publication is not authorized.

Baseline rerun: 50 backend tests pass (1.39s), one component test passes, production npm audit reports zero vulnerabilities. First build failed because the running standalone process locked .next/standalone; stopped that exact process before rebuilding. Docker CLI exists but engine pipe is unavailable. Prior live status artifacts show search, scoped discovery, desktop/mobile group flow and two OpenAI edits; these are smoke evidence, not quality evaluation.

## Trace map

`frontend/app/page.tsx` collects Intent, posts `/api/plan`, reads real NDJSON phases/decisions, renders ExperienceCard and GroupReport. Next rewrites same-origin API requests to internal FastAPI. `main.py` validates Intent and chooses fixture/live client. `planner.py` resolves each profile, performs pooled discovery, filters hard requirements, conditionally expands one page, then `negotiation.py` fetches per-member same-pool order and enumerates subsets. Runtime critic gates outputs. Results include IDs, source and missing-fact warnings. Revisions resubmit full Intent; no persistent user memory.

`/api/interpret` calls OpenAI strict-schema extraction in `llm.py`. Its field semantics require per-person budget, preservation of unrelated fields and null companion inheritance. Pydantic revalidates the response; user reviews updated controls before planning. Two live cases passed after prompt fixes, not a proof against all LLM mistakes.

## Priorities

| Priority | Issue | Action |
|---|---|---|
| P0 | No external app or public source | Prepare Heroku remote-build manifest and exact owner approval; cannot claim submission-ready |
| P0 | Anonymous provider spend/oversized requests | Add process-wide route limits, interpreter concurrency, body bound; disclose single-process limitations |
| P0 | Container not executable locally | Native build/startup regression; host build must be verified after approval |
| P1 | Group tradeoffs too buried | Show fair-versus-mean coverage per person and a clear example group after deployment gate |
| P1 | Evidence is mainly synthetic | Real live smoke exists; independent quality evaluation remains unrun |
| P1 | Discovery wording implies a feasible day | Preserve provisional disclosure and unknown facts; avoid booking/price promises |
| P2 | More domains, persistence, routing, enrichment | Defer; do not broaden architecture near deadline |

Security work keeps one Python worker and one web service. Per-process limits reset on restart and are not a hard billing cap; provider account budgets and host controls remain necessary. No account settings were changed. DevRelay community lookup was attempted but its connector was unauthenticated, so no community evidence is claimed.

## Official requirements checked

The [overview](https://qloo.devpost.com/) explicitly requires externally hosted public access and says videos are optional. The [rules](https://qloo.devpost.com/rules) require working Qloo agentic use, public licensed source, description and free judge access through November 5, 11:45 p.m. Eastern. Four criteria are equally weighted; initial viability is pass/fail. [Resources](https://qloo.devpost.com/resources) links the [official kit](https://github.com/qloo/qloo-hackathon-kit). A controlled tool workflow is our actual architecture; do not call it autonomous multi-agent reasoning.

Final release checks: 53 backend tests (1.46s), 12 desktop/mobile browser tests (49.1s), component test and production build passed. GitHub CI run 41081525719 also passed the Linux Docker build/startup. Four-profile live rehearsal returned 20 candidates with nine Qloo calls and no fair/mean objective difference. This is not a quality benchmark. Public app verification remains pending owner deployment.
