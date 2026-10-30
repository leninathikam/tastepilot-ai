# Five difficult judge questions

**1. Is this really an agent, or just a ranking formula?**

It is a bounded tool-based decision workflow. It resolves entities, requests candidate evidence, checks hard requirements, conditionally expands discovery when evidence is insufficient, scores each person's same candidate pool, selects a compromise and checks invariants. Feedback triggers replanning with retained constraints. The OpenAI component extracts intent; it is not an autonomous planner. Do not claim multi-agent reasoning or unconstrained autonomy. Evidence: planner.py, negotiation.py, streamed decisions and expansion tests.

**2. What breaks if Qloo is removed?**

The live candidate pool and all per-member ordinal taste evidence depend on Qloo. Without it, the live path fails clearly; it does not silently substitute fictional venues. A no-taste ablation keeps the same pool to isolate ranking sensitivity, so it does not measure independent retrieval quality. Named seed resolution and scoped Insights queries were verified against the hackathon API.

**3. Is your fairness proven?**

Only with respect to the stated bounded optimization objective. We maximize the least-served member's best-stop proxy, then mean coverage and tie-breakers, across subsets of at most 20 candidates and six stops. Ordinal ordering is not calibrated human satisfaction. Synthetic tests show the optimizer behaves as specified; they do not prove demographic fairness or better group enjoyment. People may reasonably prefer a different objective.

**4. Can I actually visit or afford these places?**

The app does not establish that. Live prices, date-specific hours, dietary suitability and accessibility are unknown. Confirmed plans reject unknown hard facts; provisional cultural discoveries remain clearly labeled. A group shortlist can be nonempty while confirmed stops are zero and budget completion is false. Real booking feasibility needs independent current venue verification.

**5. What evidence supports impact and reliability?**

Observed: local regression tests, production builds, live Qloo discovery/rescoring, live desktop/mobile group flows and two live OpenAI budget edits. No user study, measured retention, independent recommendation-quality baseline or commercial traction exists. Request limits and timeout guards bound a single-process demo, not a production SLA. Public availability must be proven separately after deployment; see RELEASE_FINDINGS and TEST_RESULTS for current counts.
