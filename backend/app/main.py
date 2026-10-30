import asyncio
import json
import logging
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from .models import Intent, TextRequest
from .planner import plan
from .qloo import QlooClient, IntegrationError
from .fixtures import FixtureClient
from .safety import RequestSafety

load_dotenv(Path(__file__).resolve().parents[2] / '.env')
app = FastAPI(title='TastePilot AI', version='0.1.0')
app.add_middleware(RequestSafety)
logger = logging.getLogger('tastepilot')
gate = asyncio.Semaphore(4)
interpret_gate = asyncio.Semaphore(2)


def make_client():
    mode = os.getenv('DATA_MODE', 'fixture')
    if mode == 'fixture':
        return mode, FixtureClient()
    if mode != 'live':
        raise IntegrationError('DATA_MODE must be fixture or live')
    return mode, QlooClient(os.getenv('QLOO_API_KEY'), os.getenv('QLOO_API_URL', 'https://hackathon.api.qloo.com'))


@app.middleware('http')
async def correlation(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers['X-Request-ID'] = request.state.request_id
    response.headers['Cache-Control'] = 'no-store'
    logger.info(json.dumps({'event':'request', 'id':request.state.request_id, 'method':request.method, 'status':response.status_code}))
    return response


@app.get('/api/health')
def health():
    return {'status':'ok', 'mode':os.getenv('DATA_MODE','fixture'), 'live_verified':False}


@app.post('/api/plan')
async def create_plan(intent: Intent, request: Request):
    if gate.locked():
        raise HTTPException(429, 'Planner is busy; please retry shortly')
    try:
        mode, client = make_client()
    except IntegrationError as exc:
        raise HTTPException(503, str(exc)) from None
    async def events():
        async with gate:
            try:
                async with asyncio.timeout(60):
                    async for event in plan(intent, client, mode):
                        if await request.is_disconnected():
                            return
                        yield json.dumps({**event, 'request_id':request.state.request_id}) + '\n'
            except TimeoutError:
                yield json.dumps({'type':'error','message':'Planning exceeded the 60-second limit. Narrow the profiles and retry.','request_id':request.state.request_id})+'\n'
            except IntegrationError as exc:
                yield json.dumps({'type':'error', 'message':str(exc), 'request_id':request.state.request_id})+'\n'
            except Exception:
                logger.error(json.dumps({'event':'plan_failed', 'id':request.state.request_id}))
                yield json.dumps({'type':'error', 'message':'Planning failed. Please retry.', 'request_id':request.state.request_id})+'\n'
    return StreamingResponse(events(), media_type='application/x-ndjson')


@app.post('/api/interpret')
async def interpret(body: TextRequest):
    from .llm import interpret_text
    if interpret_gate.locked():
        raise HTTPException(429, 'Interpreter is busy; use the structured controls or retry shortly')
    try:
        async with interpret_gate:
            return await interpret_text(body)
    except IntegrationError as exc:
        raise HTTPException(503, str(exc)) from None
