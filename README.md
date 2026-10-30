# TastePilot AI

**Cultural intelligence that turns personal taste into real-world experiences.**

TastePilot connects named cultural favorites to place discovery, then applies practical constraints before ranking a day out. It is built for curious travelers whose interests span music, film, food and art.

## Status â€” read first

Local implementation with an explicit fictional Chicago simulation. Live Qloo search, Chicago discovery, scoped per-person scoring and the group browser workflow were verified on October 30. Practical venue facts remain unverified. Public deployment is not complete; source publication is part of the release handoff. This is not yet a submission-ready live Qloo product. There are no claims of improved recommendation quality or real users.

## What works

- Next.js/TypeScript responsive planning workspace and FastAPI backend.
- Artist, movie, book and brand seed resolution; geographically restricted Qloo place discovery in the live adapter.
- Typed six-stage workflow, actual streamed progress, bounded retries, correlation IDs and server-only secrets.
- Strict hard-requirement exclusion; aggregate budget checks; transparent unknown facts.
- Replacement and cheaper revisions that preserve other constraints.
- Taste DNA counts derived from user inputs, evidence details and same-candidate ranking ablation.
- Fixture-only repeatable evaluation scenarios and integration/browser test suites.
- Up to four taste profiles, same-pool per-member evidence, bounded max-min group selection and mean-objective comparison.
- One conditional discovery expansion, runtime constraint critic and visible revision/source trails.

Qloo is central to live candidate generation and the ordinal taste component of ranking. Disabling that component in the ablation preserves candidate sets and constraints. Synthetic fixture results demonstrate mechanics only; live value evidence is still required.

## Architecture

Browser -> Next.js same-origin API proxy -> FastAPI -> validated intent -> exact entity resolution -> Qloo place insights -> hard constraints -> weighted ranking and diversity -> critic invariants -> source-labeled result.

The application uses a deterministic controlled pipeline rather than a multi-agent framework. Optional OpenAI intent extraction converts natural language to the same validated form. Structured controls work without an LLM. No retrieved content can execute tools.

## Local setup

Requirements: Node 20.9+ and Python 3.12+ (tested on Python 3.14). From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend/requirements.txt
Copy-Item .env.example .env # only if .env does not already exist
.\.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:3000. Backend health is /api/health and interactive schema is http://127.0.0.1:8000/docs.

## Configuration

Root `.env` is ignored. Never use NEXT_PUBLIC variables for keys.

| Variable | Purpose |
|---|---|
| DATA_MODE | fixture (default) or live; no silent live-to-fixture fallback |
| QLOO_API_KEY | Event-issued key, backend only |
| QLOO_API_URL | Approved HTTPS Qloo origin matching your issued access |
| OPENAI_API_KEY | Optional natural-language interpretation |
| OPENAI_MODEL | Optional interpreter model; default gpt-4.1-mini |
| BACKEND_URL | Next.js server-side backend origin; defaults to loopback :8000 |

After adding keys, restart the backend. Change DATA_MODE to live only when ready to exercise Qloo. Fixture named favorites include Japanese Breakfast, Radiohead, Khruangbin, Past Lives, Dune and Uniqlo. Fixture venues are fictional and only exist for Chicago. Dates do not establish opening hours.

## Testing and evaluation

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest backend/tests -q
python -m evaluation.run
python -m evaluation.group_run
python -m evaluation.live_probe # reports credential/readiness status without network calls
cd frontend
npm test
npm run build
npx playwright install chromium
# Start backend and frontend before browser tests; DATA_MODE=fixture.
npm run test:e2e
```

See docs/TEST_RESULTS.md for executed results and docs/EVALUATION.md for scope. No statistical significance or quality uplift claims are made.

## Deployment and submission

Owner-operated Heroku deployment: [open the deployment form](https://heroku.com/deploy?template=https://github.com/leninathikam/tastepilot-ai). Review the one Basic dyno ($7/month) and provider charges before deploying. See [step-by-step instructions](docs/DEPLOYMENT.md). Never paste keys into source.


See docs/DEPLOYMENT.md. Dockerfile packages a standalone Next frontend and an internal FastAPI backend on one public port. Container execution is not verified: the local Docker engine is unavailable. CI is configured but has not run remotely. No paid resources are authorized. Publishing requires explicit owner approval. See SUBMISSION_READINESS.md for release gates.

## Limits

Live place prices, booking availability, hours, routing, accessibility and dietary suitability are not verified. Unknown costs are excluded from confirmed plans and surfaced as provisional discoveries, including provisional group compromises. No live venue enrichment provider is connected. A live result can therefore contain a useful shortlist but no confirmed itinerary. Event quota, expiry and data retention rights need confirmation. Search resolves unique exact names only. Group coverage is an algorithmic proxy, not measured satisfaction. No timed routing, human quality evaluation or LLM-only benchmark exists yet. No user profiles are persisted; request contents are not logged. Public hosting needs edge rate limiting and operational monitoring.

MIT license covers project code, not Qloo data or trademarks.
