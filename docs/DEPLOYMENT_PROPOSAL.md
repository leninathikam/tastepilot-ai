# Owner decision

Owner authorized preparation and public GitHub push and will deploy personally. No Heroku resource was created. The proposal below is historical context; see DEPLOYMENT.md for the handoff.

# Heroku deployment proposal — approval required

Owner selected Heroku. The Render proposal and blueprint are superseded.

**Architecture:** one Cedar container-stack app, one Basic web dyno, no add-ons/database/custom domain. heroku.yml builds the existing Dockerfile remotely, so local Docker is unnecessary. scripts/serve.py binds Next to Heroku PORT and FastAPI to loopback 8000; both stop together. Public HTTPS URL is assigned by Heroku; the exact URL will be recorded only after verification.

**Cost:** Basic is listed at $7/month and stays awake. Eco is $5/month but sleeps after 30 idle minutes. Recommend Basic for judges. Taxes and Qloo/OpenAI usage are separate. No upgrade, payment method or paid resource has been created. Source: https://www.heroku.com/pricing/ (checked October 30).

**Environment names:** DATA_MODE=live, QLOO_API_URL, QLOO_API_KEY, OPENAI_API_KEY, OPENAI_MODEL. Heroku supplies PORT. Store keys in Heroku config vars, never source/build arguments. The host receives server credentials. Existing API costs continue; account spending controls remain the owner's responsibility.

**Public source:** proposed leninathikam/tastepilot-ai on GitHub. CLI is authenticated; repository publication still needs approval. Source is secret-scanned and baseline is archived locally.

**Security:** anonymous demo requests can consume provider quotas. Added global per-process limits (60 planner requests/minute; 10 interpreter requests/minute and 200/day), 32 KiB body bound, interpreter concurrency two, planner concurrency four, server-only credentials, non-root container and browser security headers. Limits reset on restart and are not hard billing caps. No stored profiles or prompt logs. Live discovery sends favorite names, cultural IDs and destination to Qloo; interpretation sends planning fields/text to OpenAI when invoked. No broad CORS. One instance/worker is required for these local limits.

**Exact approval needed:** create/publicly expose the Heroku app on Basic ($7/month), store existing provider keys as config vars, and publish reviewed source to the proposed GitHub repository. Identify the Heroku account/team and desired existing app or new app name. No local Heroku login or CLI was found; owner login is required. Do not send account passwords/API tokens in chat.

After approval and login: publish code, build remotely on Heroku, start one web dyno, verify HTTPS, test fresh desktop/mobile sessions with live Qloo and constraints, record URLs/commit. Container build and public availability remain unverified until these checks pass.
