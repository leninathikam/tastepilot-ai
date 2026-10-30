import asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.app.safety import RequestSafety


def test_limits_expire_and_do_not_depend_on_forwarded_ip():
    now=[0.0]; app=FastAPI()
    app.add_middleware(RequestSafety,plan_per_minute=1,clock=lambda:now[0])
    @app.post('/api/plan')
    def plan(): return {'ok':True}
    with TestClient(app) as client:
        assert client.post('/api/plan',json={}).status_code==200
        blocked=client.post('/api/plan',json={},headers={'X-Forwarded-For':'different'})
        assert blocked.status_code==429 and blocked.headers['retry-after']=='61'
        now[0]=61
        assert client.post('/api/plan',json={}).status_code==200


def test_chunked_oversized_request_rejected_before_application():
    called=[];sent=[];chunks=iter([{'type':'http.request','body':b'123','more_body':True},{'type':'http.request','body':b'456','more_body':False}])
    async def app(*args): called.append(True)
    async def receive(): return next(chunks)
    async def send(message): sent.append(message)
    asyncio.run(RequestSafety(app,max_bytes=5)({'type':'http','method':'POST','path':'/api/plan'},receive,send))
    assert not called and sent[0]['status']==413


def test_daily_interpreter_limit_leaves_planning_available():
    now=[0.0];app=FastAPI()
    app.add_middleware(RequestSafety,interpret_per_minute=5,interpret_per_day=1,clock=lambda:now[0])
    @app.post('/api/interpret')
    def interpret(): return {'ok':True}
    @app.post('/api/plan')
    def plan(): return {'ok':True}
    with TestClient(app) as client:
        assert client.post('/api/interpret',json={}).status_code==200
        now[0]=61
        assert client.post('/api/interpret',json={}).status_code==429
        assert client.post('/api/plan',json={}).status_code==200
