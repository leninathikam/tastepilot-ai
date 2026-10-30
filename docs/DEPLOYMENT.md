# Deploy TastePilot to Heroku

The owner will deploy. No Heroku app or dyno has been created by this agent. The repository includes heroku.yml, app.json and a multi-stage Dockerfile; Heroku builds remotely, so you do not need a working local Docker engine.

## Browser deployment

1. Open the [Heroku deployment form](https://heroku.com/deploy?template=https://github.com/leninathikam/tastepilot-ai). Sign into your account and choose an app name. This targets Cedar/container; Heroku Buttons do not support Fir.
2. Review the Basic web dyno: currently $7/month, always on. API charges and applicable taxes are separate. No database or add-ons are requested. The app.json formation requests one Basic dyno; confirm charges before you click Deploy.
3. Enter QLOO_API_KEY and, optionally, OPENAI_API_KEY into Heroku's configuration fields. Keep DATA_MODE=live, QLOO_API_URL=https://hackathon.api.qloo.com and OPENAI_MODEL=gpt-4.1-mini. Do not put secrets in GitHub, screenshots or chat.
4. Deploy and inspect the build/release result. Open the assigned HTTPS app URL. The exact URL is not known in advance; do not submit the deployment form URL as your demo.
5. Verify /api/health reports live mode, then use the four-person example and Build my day. Confirm real Qloo discoveries, per-person evidence and provisional price labels. Add Alex's access requirement and replan: unknown access must not pass.
6. Keep the app accessible through November 5, 2026, 11:45 p.m. Eastern. Set provider-account spending controls and monitor availability. Share the deployed app URL for independent verification.

## Existing app / CLI alternative

Use an existing owner-selected Cedar app, set its stack to container, and link this source. With authenticated Heroku CLI and a local clone:

```sh
heroku git:remote --app YOUR_APP_NAME
heroku stack:set container --app YOUR_APP_NAME
# Set API keys in Dashboard > Settings > Config Vars, not shell history.
git push heroku HEAD:main
heroku ps:scale web=1:basic --app YOUR_APP_NAME
heroku open --app YOUR_APP_NAME
```

Changing an existing app replaces its deployment: use a dedicated app. If GitHub integration is used instead, explicitly set the stack to container before deploying the branch. Ordinary language auto-detection is not the intended path.

## Runtime and safety

Heroku supplies PORT. scripts/serve.py starts Next on that public port and FastAPI on loopback 8000; no second public service, database or worker is needed. Browser API calls are same-origin. The container is non-root; only its image-cache directory is writable across runtime UIDs. Local npm start serves standalone output after copying assets.

Global per-process limits are 60 planner requests/minute, 10 interpreter requests/minute and 200 interpreter requests/day. Body cap is 32 KiB. Concurrency is four planners and two interpreter calls. These reset when Heroku restarts a dyno and are not hard billing caps. Keep one instance/worker unless replacing the limiter with a shared store. A limit failure should display a clear error; structured controls work independently of OpenAI.

## Public verification command

After npm ci and Playwright installation, set JUDGE_BASE_URL to the deployed HTTPS URL and run `node scripts/judge_smoke.cjs`. This makes live Qloo requests and captures authentic screenshots plus safe aggregate checks in evaluation/results/judge_smoke.json. Review results before submission. Provider-failure regression uses isolated request interception in the Playwright suite; it does not simulate an actual upstream outage.

Public deployment is unverified until the real host build and clean-session desktop/mobile checks pass. Local build/startup and fixture tests are not proof of Heroku deployment success.

Sources: https://devcenter.heroku.com/articles/build-docker-images-heroku-yml, https://devcenter.heroku.com/articles/app-json-schema, https://devcenter.heroku.com/articles/heroku-button, https://www.heroku.com/pricing/.
