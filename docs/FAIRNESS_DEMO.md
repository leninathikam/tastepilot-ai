# Reproducible compromise example and observed live result

The four-person UI example uses real named seeds in live mode. On October 30 its nine-call run returned 20 places and chose the same one-stop option under both objectives. The table shows zero change for every person; do not describe this live run as a fairness improvement. See `evaluation/results/judge_smoke.json` and screenshots.

To inspect an actual deterministic objective difference, run `python -m evaluation.group_run`. The `one-stop` scenario uses **authored fictional fixtures**, not Qloo data: organizer Japanese Breakfast with Korean-food interest; Music friend Radiohead; Film friend Past Lives; Chicago, three people, $150/person, one stop.

| Profile | Mean-objective choice | Max-min choice | Change |
|---|---:|---:|---:|
| Organizer | 1.00 | 0.39 | -0.61 |
| Music friend | 0.13 | 0.26 | +0.13 |
| Film friend | 0.39 | 0.65 | +0.26 |

Mean selects fictional `fixture:0`; max-min selects `fixture:2`. The minimum proxy rises from 0.13 to 0.26 while mean coverage falls from about 0.507 to 0.433. This is a transparent sacrifice under the objective, not evidence that real people enjoy the fair option more. Those numbers are generated from the declared synthetic order/tag matrix. The two-stop scenario also differs, with complete inputs and outputs saved in group_raw.json.

Use this only as a labeled algorithm demonstration alongside the live API workflow. Never present the fictional scenario as measured Qloo uplift. Live ordering can change, and both methods may agree.
