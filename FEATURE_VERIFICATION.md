# Feature verification — October 30, 2026

Statuses describe actual implementation and evidence, not intended features. Unit/transport mocks do not establish live provider behavior.

| Feature | Status | Evidence / boundary |
|---|---|---|
| Editorial landing, taste profile, planning and result UI | Fully implemented and verified locally | Production build, component test; browser workflow results in TEST_RESULTS |
| Licensed imagery and responsive styling | Fully implemented and verified locally | Local optimized Pexels assets, public/images/CREDITS.md, mobile overflow/image tests; inspiration imagery labeled and restricted to fixtures |
| Keyboard entry, reduced motion, errors | Fully implemented and verified within tested scope | Browser checks; not a complete WCAG audit |
| Typed intent and request validation | Fully implemented and verified | Pydantic schema, invalid budgets/profiles and API tests |
| Qloo search and geographically scoped discovery | Fully implemented and verified for the smoke scenario | Live search and 20 Chicago results; tests cover transport failures |
| Artist/movie/book/brand to place discovery | Partially verified live | Artist/movie default profiles exercised; book/brand live scenarios not exercised; unique exact names only |
| Fictional Chicago venue catalog and taste order | Mocked or simulated | Six authored venues and seed-order matrix; explicitly labeled synthetic |
| Group profiles and shared constraints | Fully implemented and verified locally | Up to four profiles; strictest budget, all diets, any access requirement; tests/test_negotiation.py |
| Per-member same-pool Qloo queries | Fully implemented and verified for the smoke scenario | Live scoped IDs and full two-profile group run; transport tests check IDs and privacy |
| Fair group subset optimizer | Fully implemented and verified on synthetic data | Bounded combinations, max-min best-stop coverage; crafted mean-vs-fair test and 15 scenarios |
| Satisfaction prediction | Missing | Coverage is an ordinal proxy, not observed or calibrated satisfaction |
| Adaptive tool planning | Partially implemented | Conditional page-two expansion, explicit decisions, hard runtime critic; no autonomous general-purpose agent or repeated repair loop |
| Replace / cheaper revisions | Fully implemented locally | Reruns preserved intent; shows added/removed IDs; no persistent memory |
| Explainable provenance | Partially implemented | Source, IDs, ordinal rank, missing evidence and decision trail; no causal seed attribution |
| Practical venue verification | Missing | No current price, booking, dated hours or accessibility enrichment |
| Confirmed live itinerary | Broken for the original confirmed-itinerary promise | Live costs remain unknown and are excluded; provisional discovery is now an explicit usable outcome, not a verified visit plan |
| Natural-language form interpretation | Verified for two live budget-edit cases | Strict-schema OpenAI wrapper; per-person/group-total and preservation checks passed; not an autonomous planning agent |
| Same-pool taste ablation | Implemented; synthetic evaluation and live execution verified | Single and group evaluation; live value unknown |
| Qloo-versus-LLM quality benchmark | Missing | No live corpus, LLM-only baseline or blinded human review |
| Runtime invariants / timeout / retry bounds | Fully implemented within tested scope | Budget/source/duplicates/requirements checked without assert; 60-second plan timeout; long Retry-After fails rather than retrying early |
| CI and combined deployment packaging | Implemented but not verified | Workflow and multi-stage Dockerfile exist; no remote CI or running Docker engine |
| Public repository / public hosted demo | Missing | No Git remote or deployed URL |
| Authentication, persistence, distributed rate limiting | Missing | Not needed to demonstrate the core locally; operational safeguards remain before public access |

See EVALUATION_RESULTS.md for measured results and SUBMISSION_READINESS.md for remaining gates.
