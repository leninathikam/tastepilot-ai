# Evaluation results — October 30, 2026

## Executed checks

- `python -m pytest backend/tests -q`: **50 passed**, 0.69 seconds on final regression. One upstream Starlette/httpx deprecation warning.
- `npm run build`: **passed**, including TypeScript and static generation (Next 16.4.3).
- `npm test -- --run`: **1 passed** (Taste DNA component).
- `python -m evaluation.run`: completed 15 synthetic scenarios.
- `python -m evaluation.group_run`: completed 15 synthetic scenarios.
- `python -m evaluation.live_probe --execute`: **passed**, three live requests; search, 20 Chicago places and a five-ID scoped rescore.
- Fixture browser regression: **10 passed** across desktop/mobile, 2.0 minutes. Live desktop group smoke: passed, six Qloo calls, 20 candidates, two profiles, three provisional group choices, zero confirmed stops, budget incomplete.
- Docker engine check failed: named pipe dockerDesktopLinuxEngine unavailable. Container build/runtime not verified.

## Single-profile fixture evaluation

15/15 budget checks, 15/15 hard-constraint checks, 15/15 stable ordering. Mean exact-interest coverage 0.8; 12 scenarios change ranking after removing the taste component. Qloo calls: zero. This ablation retains the candidate pool; it does not compare Qloo retrieval with an independent recommender. See evaluation/results/aggregate.json and raw outputs.

## Group fixture evaluation

| Measure | Observed |
|---|---:|
| Expected outcomes | 15/15 |
| Completed planning responses | 14 |
| Nonempty itineraries | 12 |
| Empty itineraries | 2 |
| Expected unresolved-profile error | 1 |
| Budget / hard-constraint checks | 14/14 each |
| Stable repeat selections | 14/14 |
| Least-served coverage no worse than mean objective | 14/14 |
| Strict improvement of least-served proxy | 2/14 |
| Selection changed by removing taste signals | 8/14 |

Source: evaluation/results/group_aggregate.json, group_raw.json and datasets/group_scenarios.json. Scenarios include differing stop counts, budgets, dietary/access constraints, exclusion, unknown hours, unsupported location and unresolved preference.

The optimizer maximizes the minimum member's best represented stop, then mean coverage, diversity, cardinality and lower known cost. Per-member signals use ordered results plus exact tag alignment. The mean comparator uses the same pool and constraints with a different objective. Its comparison tests a deliberate optimization policy: **it is not independent evidence of recommendation quality**. Empty plans passing constraints are not successful trip plans. Synthetic named-favorite effects come from an authored matrix.

## Not measured

No live affinity quality, human satisfaction, demographic fairness, independent LLM baseline, factual-claim review, public latency/load or provider spend has been measured. Do not claim a Qloo uplift, accuracy percentage or production readiness.

## Next reproducible gate

Credentials are configured in ignored root .env. To repeat the bounded check, run `python -m evaluation.live_probe --execute` to check search, discovery and same-pool rescore with bounded calls; inspect safe status output. Then run the actual UI in live mode and evaluate returned IDs and provisional disclosures. This smoke probe alone does not establish experience quality. Before reporting Qloo-versus-baseline gains, record a permitted live evaluation set, keep constraints/pool consistent for ablations, add an independently defined baseline, and have reviewers judge relevance without seeing method labels.

Live mobile follow-up (October 30): standalone Next server startup and the full two-profile browser workflow passed; six Qloo calls, 20 candidates, three provisional choices, no horizontal overflow, zero confirmed stops and budget incomplete. Safe status: evaluation/results/live_browser_mobile_status.json. No raw response corpus saved.

OpenAI live verification (October 30): gpt-4.1-mini passed two requests through the running Next/FastAPI endpoint: $75/person remained 75; $90 total for three became 30/person. All other fields, including companion constraints and inherited budgets, were preserved. Initial probes revealed budget-unit and companion-preservation errors; extraction instructions were corrected before the passing rerun. This verifies tested intent extraction cases, not general accuracy or an LLM-only recommendation baseline. Evidence: evaluation/results/live_openai_status.json.

Final release checks: 53 backend tests (1.46s), 12 desktop/mobile browser tests (49.1s), component test and production build passed. GitHub CI run 41081525719 also passed the Linux Docker build/startup. Four-profile live rehearsal returned 20 candidates with nine Qloo calls and no fair/mean objective difference. This is not a quality benchmark. Public app verification remains pending owner deployment.
