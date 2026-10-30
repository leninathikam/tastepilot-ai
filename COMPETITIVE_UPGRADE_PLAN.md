# Competitive upgrade plan

## Priority and feasibility

| Priority | Work | Judging impact | Effort | Risk / dependency |
|---|---|---|---|---|
| P0 | Real Qloo smoke test, correct response mapping | Eligibility-critical | Small once key exists | Blocked on owner key; no invented success |
| P0 | Public source + accessible app | Eligibility-critical | Moderate | Owner publishing authorization, host account and free capacity |
| P0 | Truthful discovery vs verified itinerary boundary | High | Small | Unknown costs/hours remain provisional; no false guarantees |
| P1 | Per-member cultural profiles, same-pool Qloo queries, bounded max-min compromise | High differentiation | Moderate | API quota and cross-query missing evidence; mock/live paths separated |
| P1 | Constraint-driven one-page discovery expansion and runtime critic | High technology | Small–moderate | Never relax hard requirements; cap calls and search size |
| P1 | Evidence ledger + per-member tradeoffs + revision change report | High trust | Small–moderate | No causal/personal satisfaction claims |
| P1 | Group optimizer vs mean-preference and no-taste ablations; adversarial scenarios | High credibility | Moderate | Synthetic evidence proves mechanics only |
| P1 | Executable live probe + explicit baseline status | High credibility | Small | Live/LLM comparison cannot run without credentials |
| P2 | Timed routing, verified places enrichment, booking | High product value | Large | New provider, data freshness and licensing; avoid unfinished integration |
| P2 | Further visual polish | Low incremental value | Small | Existing redesigned UI already passes browser checks |

## Selected implementation

Add up to three companions alongside the organizer's existing profile. Resolve each person's named entities; query a pooled place set, then retrieve per-person ordering over the SAME candidate IDs using documented `filter.results.entities`. Never average raw affinity values across queries. Convert each member's returned ordering to a transparent ordinal proxy; a missing result is unknown, not dislike. Aliases and personal requirements stay local and are never sent to Qloo.

For groups, enumerate bounded candidate subsets and maximize the least-served member's best-stop proxy, then mean coverage, diversity and cardinality; break remaining ties by lower cost and stable IDs. At most 20 scored candidates and 6 selected stops. Compare against a mean-coverage objective and an identical-candidate no-taste ablation. Label all proxies as algorithmic coverage, not human satisfaction.

Hard requirements combine across the group. Fail closed on unknown facts. If a complete cost-feasible itinerary is impossible, separately show an explicitly provisional group discovery shortlist without calling its unknown costs budget-compliant.

On insufficient eligible/affordable options, fetch at most one additional documented page, without changing geography or hard constraints. Emit a real decision event explaining the trigger and outcome. Runtime critic checks duplicate IDs, budgets, requirements and source labels; do not rely on optimizable assertions.

Keep revisions stateless but compare returned IDs/constraint changes to the previous result in the UI. No cross-user memory or database needed. Add local tests and judge-facing evidence files before any further features.

## Release gates

October 30 execution update: selected group, evidence, bounded adaptive planning, fixture evaluation, UI, CI and packaging work is implemented. Live probe and group browser smoke now pass after fixing the observed search type schema. Highest remaining priorities are public release authorization/account, container verification, deployment and a truthful recorded live demo. Practical enrichment and independent quality evaluation remain deferred; no LLM baseline result is claimed.

No paid provisioning or public publishing until authorized. Keys remain in ignored .env. A fixture-only deployed site is not sufficient to claim meaningful live Qloo integration. If time runs out, submit only functionality actually validated; do not claim the product is complete.
