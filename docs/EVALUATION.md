# Evaluation methodology

Run `python -m evaluation.run` from root. Fifteen deterministic synthetic scenarios vary budget, group size, interests, access and vegetarian requirements. Inputs, complete outputs and aggregates are saved in evaluation/. Every fixture is authored fictional data, not an API recording. Unknown-hour exclusion and failure paths are covered by backend tests.

Metrics: cumulative budget satisfaction; required accessibility/dietary checks; exact normalized tag coverage against candidate tags; category count; repeated ordering stability; fixture label coverage; backend latency; actual Qloo request count. Empty plans pass safety constraints vacuously but have zero interest coverage; do not interpret that as planning success. Prices are per-person fictional USD values, excluding transport/tax.

Ablation uses identical candidate sets, filters and category-diversity algorithm, with taste weight set to zero. It establishes sensitivity of the ranker, not real Qloo quality. Name sorting breaks ties deterministically by ID. Source ordering is a relative within-query signal, not a probability.

LLM-only baseline, blinded preference ratings, unsupported-claim audit and operating cost measurement have NOT been run. Cost and unsupported-claim-rate fields remain null. Real-world enrichment is absent. No significance or superiority claims are justified. Before submission, run both live Qloo and a separately labeled LLM baseline on identical inputs; preserve authorized evidence and obtain blinded ratings with a preregistered rubric.
