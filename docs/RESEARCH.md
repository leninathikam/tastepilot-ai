# Research and feasibility gate

Reviewed 2026-10-28 (America/New_York). Empty repository; Python 3.14 and Node 25 available. No configured provider credentials at inspection. Never include keys in research artifacts.

Official sources:
- https://qloo.devpost.com/rules and https://qloo.devpost.com/: deadline October 30, 2026 11:45 PM EDT; functional externally hosted application, public source and visible open-source license required. Four equally weighted judging criteria. Eligibility must be checked by the entrant.
- https://github.com/qloo/docs-public at d4a0eb978518f7fb404993d1509d11b21239ada6: reference/get-search.md, reference/parameters.md, reference/api-onboarding.md, reference/basic-insights-use-case.md.
- https://github.com/qloo/qloo-hackathon-kit: docs/API_ACCESS.md and docs/SAFE_USE.md.

The supplied docs.qloo.com guide could not be resolved; official GitHub documentation was retrieved instead. Context7 tools unavailable; consulted official Next.js installation and FastAPI testing documentation. DevRelay research attempted but connector is not authenticated.

Feasible: named artist/movie/book/brand preferences -> resolved entity IDs -> place insights restricted to destination. Broad cuisines/genres should not be silently treated as named entities. We retain explicit interests for transparent local tag matching. Unambiguous exact-name resolution only in initial release; ask users for precise names if no match.

Not established: reliable event inventory, booking availability, actual prices, accessibility or dietary guarantees. Therefore output is a discovery shortlist/provisional day plan until these facts are verified. Fixture mode uses fictional venues and synthetic affinities, never represented as Qloo evidence. Live response validation requires a credential.

Gate: proceed with documented adapter, conservative unknown-data handling and fixture development. Public submission readiness remains blocked on live verification, deployment authorization and practical-data coverage. Do not claim eligibility or performance improvements.

Optional interpreter contract checked against https://developers.openai.com/api/docs/guides/structured-outputs and https://developers.openai.com/api/docs/models/gpt-4.1-mini. Uses strict JSON Schema plus Pydantic validation and bounded output tokens; mocked provider tests do not establish live account access.
