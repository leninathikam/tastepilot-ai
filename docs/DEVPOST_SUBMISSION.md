# TastePilot AI — A day that feels like you

**Draft, not submitted. Remove all readiness blockers before publication.**

## Pitch
An AI group decision workflow that uses cultural intelligence to resolve conflicting tastes fairly and transparently.

## Inspiration and audience
Travel search divides people into categories: restaurants, attractions, shows. People do not experience taste that way. A favorite artist, a memorable film and a preferred cuisine all inform what makes a day feel personal. TastePilot is for travelers and small groups who want to explore beyond generic lists while understanding why something was suggested.

## What it does
Choose a destination, date, group size and budget. Add named artists, films, books or brands and explicit activity interests. Follow the backend's actual resolution, discovery, validation, ranking and review steps. Inspect evidence, replace a stop or reduce spending while retaining preferences. Taste DNA displays the inputs you provided rather than inventing personality traits.

Start with the four-person example: Japanese Breakfast, Radiohead, Khruangbin and Past Lives. Compare the same candidates across those profiles, inspect the max-min compromise against the mean-preference choice, and see each person's proxy gain or sacrifice. When the choices agree, the app says so. Add an access or dietary requirement to replan without silently weakening it. Live outputs are cultural discoveries, not confirmed itineraries.

## How Qloo is used
The adapter resolves named entities with /search, passes the returned IDs into /v2/insights for places, and restricts geography with the documented location filter. Qloo response order contributes a relative taste signal to ranking. A same-candidate ablation exposes which rankings change without that component. Affinities are aggregate cultural signals, not promises of individual satisfaction.

## Implementation
Next.js, React and TypeScript frontend; Python, FastAPI, Pydantic, and Modal serverless backend intelligence. Real-time Qloo cultural discovery feeds a high-performance Modal serverless optimization function that calculates combinatorial max-min fairness, candidate satisfaction vectors, and leave-one-member-out counterfactual explanations. Resilient timeout and local fallback ensure uninterrupted service if remote compute is unavailable. Optional schema-validated LLM intent extraction sits behind a replaceable provider boundary.

## Challenges and honest current state
Missing practical venue facts (exact operating hours, live pricing, wheelchair access) are treated as unverified rather than claiming safety. A high taste score cannot override a hard requirement. The application is deployed live to Heroku with serverless compute on Modal, fully exercising Qloo search and discovery in production.

## Evaluation
See evaluation/results/aggregate.json and docs/TEST_RESULTS.md for executed local evidence. Synthetic ranking changes demonstrate system mechanics only. There is no measured real-world Qloo uplift, human preference study, operating cost claim or LLM-only baseline result.

## Impact and next steps
The intended benefit is less repetitive search and more transparent personalization. Group negotiation now compares bounded max-min and mean-coverage selections with per-member evidence. Next steps are practical venue verification, public hosting and blinded evaluation.

## Required links
- Public application: https://tastepilot-ai-43e15cc919d5.herokuapp.com/
- Public source repository: https://github.com/leninathikam/tastepilot-ai
- License: MIT, LICENSE in repository root
- Setup and testing: README.md

Built with AI coding assistance under the project owner's direction. No invented users, traction or testimonials.
