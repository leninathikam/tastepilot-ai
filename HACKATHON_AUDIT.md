# TastePilot hackathon audit — October 29, 2026

## Post-upgrade addendum — October 30

The baseline findings below are preserved as the before-state. Group profiles, same-pool evidence, bounded max-min subset negotiation, mean/no-taste comparisons, shared constraints, conditional one-page expansion, runtime critic and revision summaries are now implemented. Fixture favorites now affect synthetic ordering. CI and combined deployment packaging were added; neither remote CI nor container execution is verified.

Live credentials enabled a real check and exposed a parser bug missed by mocks: Qloo search supplies `types`, not necessarily `subtype`. The adapter now accepts the validated type representations and has regression coverage. A three-call live probe and full six-call group browser workflow passed: 20 places and three provisional group choices for two profiles. Practical venue facts remain unknown; zero confirmed stops is an intentional limitation, not evidence of a completed itinerary.

Current evidence: 50 backend tests, one component test, production build and 10 fixture desktop/mobile browser tests pass. Thirty synthetic evaluation scenarios are recorded separately from live smoke tests. Current personal score estimates: technology 6/10, design 7/10, impact 4/10, idea 6/10. No public URL/repository or independent quality benchmark exists. See FEATURE_VERIFICATION.md, EVALUATION_RESULTS.md and SUBMISSION_READINESS.md for the current release state.

## Verdict before upgrades

Not submission-ready. The redesigned UI is credible; the demonstrated intelligence is still a six-venue fictional simulation. Missing credentials and deployment are eligibility-level blockers. More agents or more attractive cards cannot compensate for a live product that has never been exercised.

## Scope and evidence

Inspected all authored application modules, UI components/styles, TypeScript types, test suites, evaluation generator/data/aggregates, dependency manifests, Next proxy, Dockerfile, ignore rules and existing delivery documents. Excluded generated build output, dependency implementations and downloaded reference repositories from the authored-code audit. Presence-only credential inspection found Qloo/OpenAI placeholders and fixture mode. `git remote -v` returned no remotes. Baseline rerun: 35 backend tests passed, one existing upstream deprecation warning. Earlier redesign evidence: production build, component test and 8 browser checks passed.

## Findings

1. **Critical — live itinerary structurally empty.** `qloo.py::discover` never populates cost, availability, accessibility or dietary facts. `planner.py::select` excludes unknown cost. All live candidates therefore remain alternatives, regardless of API success. There is no practical venue-verification integration.
2. **High — fixture personalization is invariant.** `fixtures.py::discover` ignores supplied IDs and returns the same six fictional venues in the same order. Named favorites have no influence in the demonstrated fixture path. This is explicitly labeled, but cannot prove Qloo value.
3. **High — no group negotiation.** `Intent.party_size` only multiplies subtotal. No member profiles, per-member evidence, fairness objective, conflicting requirements or tradeoff explanation exist at baseline.
4. **High — limited agentic depth.** Six genuine progress events wrap a linear procedure. Resolution and discovery are tools, but no conditional expansion, critic repair, clarification policy or failure-aware replanning exists. The critic is two Python assertions, which disappear under `python -O`. Do not market this as seven autonomous agents.
5. **High — no empirical Qloo advantage.** `evaluation/run.py` measures fixture constraints, substring tag coverage and repeat ordering. Its baseline is a same-candidate taste-weight ablation, not LLM-only generation; candidate generation is still Qloo-dependent in a live ablation. No live outputs, human review, factual-claim audit or costs are recorded. Empty plans can pass constraints vacuously.
6. **High — no public product.** No Git remote, deployed URL or deployment record. Dockerfile only packages backend and defaults to fixture mode. Frontend requires a separate Next host/proxy configuration. No CI or release smoke test at baseline.
7. **Medium — weak ranking and provenance.** Uses ordinal response order rather than documented raw affinity semantics (honest but coarse). Explicit alignment uses substring matching; live candidates all have category `place`, so category-diversity selection has no useful effect. Entity IDs and source URLs survive, but individual seed contributions and a structured decision trail do not.
8. **Medium — revision is a stateless rerun.** Cheaper/replacement controls preserve intent but rerun every lookup, do not explain differences, and cannot replace provisional live discoveries. No timed scheduling, travel optimization, reservation or date-specific verification.
9. **Medium — provider wrapper is narrow.** `llm.py` is a genuine strict-schema intent extractor, tested through mocks. It does not plan, call Qloo or assess evidence; it is not an agent. No live provider test. Group and unsupported advanced instructions must not be silently represented as supported.
10. **Medium — operational hardening incomplete.** Semaphore bounds active planner runs but is not a global rate limiter. `/interpret` is unguarded. Rate-limit delay clamping can retry earlier than server Retry-After. Health hardcodes live_verified=false. No persistence, monitoring or distributed abuse controls.
11. **Design — strongest area.** Consistent consumer UI, licensed local optimized photos, mobile layouts, source disclosure and keyboard/reduced-motion tests. Taste DNA is an input-count visualization, not inferred taste modeling. Hardcoded fixture copy/photos are correctly labeled; no real venue photos are mapped.

## Judge estimates (my estimates, not official scores)

| Criterion | Before upgrades | Evidence |
|---|---:|---|
| Technological implementation | 3/10 | Tested deterministic foundation; no verified Qloo run; no adaptive group logic |
| Design | 7/10 | Coherent responsive consumer design; live core experience incomplete |
| Potential impact | 3/10 | Plausible traveler problem; no usable verified live day or user evidence |
| Quality of idea | 4/10 | Taste-to-travel is familiar; no implemented group compromise differentiator |

These are code/demo readiness estimates, not predicted placements. Official rules use equally weighted criteria and a viability gate. Source: https://qloo.devpost.com/rules, inspected October 29. Deadline: October 30, 2026 at 11:45 PM EDT. A public repository, open-source license and functioning accessible demo are required; the overview additionally calls for externally published hosting.

Judges may reject at the viability gate without a working Qloo demo. They may overlook it as another itinerary wrapper if all visible taste claims derive from authored fixtures. A defensible differentiator is a small-group planner that exposes who each suggestion serves and how a cheaper/replacement revision changes the compromise, grounded in actual per-member Qloo tool responses.

## Scope decision

Preserve the UI and API boundaries. Implement one bounded group-negotiation extension, structured evidence/decision traces and counterfactual evaluation. Keep unknown real-world facts unknown. Live validation and authorized publishing outrank further polish. See COMPETITIVE_UPGRADE_PLAN.md and the post-upgrade readiness report for what actually shipped.
