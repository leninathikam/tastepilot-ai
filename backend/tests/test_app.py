import asyncio
import json
from datetime import date
import httpx
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models import Intent, Candidate, Seed
from backend.app.qloo import QlooClient, IntegrationError, rows
from backend.app.fixtures import FixtureClient
from backend.app.planner import plan, select, validate


@pytest.fixture(autouse=True)
def fixture_mode(monkeypatch):
    monkeypatch.setenv('DATA_MODE','fixture')


@pytest.fixture
def intent():
    return Intent(date=date(2026,10,31), seeds=[Seed(name='Japanese Breakfast')],
                  interests=['Korean food','indie music','contemporary art'])


def run(intent, client=None, mode='fixture'):
    async def collect():
        return [e async for e in plan(intent, client or FixtureClient(), mode)]
    return asyncio.run(collect())


def test_end_to_end_stream_and_revision(intent):
    with TestClient(app) as client:
        response = client.post('/api/plan',json=intent.model_dump(mode='json'))
        assert response.status_code == 200 and response.headers['x-request-id']
        events = [json.loads(x) for x in response.text.splitlines()]
        assert [e['phase'] for e in events[:-1]] == ['intent','taste','discovery','validation','ranking','review']
        first = events[-1]
        assert len(first['itinerary']) == 3
        assert first['budget']['known_per_person'] == 72
        assert first['budget']['known_group_total'] == 216
        assert first['metrics']['qloo_calls'] == 0
        revised = {**first['intent'], 'budget':20, 'excluded_ids':[first['itinerary'][0]['id']]}
        second = json.loads(client.post('/api/plan',json=revised).text.splitlines()[-1])
        assert second['budget']['known_per_person'] <= 20
        assert first['itinerary'][0]['id'] not in [x['id'] for x in second['itinerary']]
        assert second['intent']['seeds'] == first['intent']['seeds']
        third = {**second['intent'],'require_verified_hours':True}
        result = json.loads(client.post('/api/plan',json=third).text.splitlines()[-1])
        assert result['itinerary'] == []


@pytest.mark.parametrize('field,value',[('budget',-1),('party_size',0),('date','bad'),('seeds',[{'name':'','category':'artist'}]),('destination','')])
def test_input_validation(intent,field,value):
    payload = intent.model_dump(mode='json'); payload[field]=value
    assert TestClient(app).post('/api/plan',json=payload).status_code == 422


def test_live_missing_key_does_not_fallback(intent,monkeypatch):
    monkeypatch.setenv('DATA_MODE','live');monkeypatch.setenv('QLOO_API_KEY','replace_placeholder')
    response=TestClient(app).post('/api/plan',json=intent.model_dump(mode='json'))
    assert response.status_code==503


def test_no_llm_reports_actionable_error(intent,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','')
    r=TestClient(app).post('/api/interpret',json={'text':'Make it cheaper','current':intent.model_dump(mode='json')})
    assert r.status_code==503 and 'controls' in r.json()['detail']


def test_unknown_resolution(intent):
    intent.seeds=[Seed(name='invented performer')]
    with pytest.raises(IntegrationError,match='No unambiguous'):
        run(intent)


def test_fixture_city_scope(intent):
    intent.destination='Paris'
    assert run(intent)[-1]['itinerary']==[]


def test_constraints_and_unknown_cost(intent):
    c=Candidate(id='x',name='x',source='qloo',taste_rank=1,taste_score=1)
    assert select([c],intent)[0]==[]
    intent.accessible=True
    assert 'Step-free access not confirmed' in validate(c,intent)
    intent.dietary='vegan'
    assert 'Vegan requirement not confirmed' in validate(c,intent)
    intent.require_verified_hours=True
    assert len(validate(c,intent))==3


def test_hard_constraint_beats_taste(intent):
    intent.accessible=True
    result=run(intent)[-1]
    assert 'fixture:3' in [x['id'] for x in result['rejected']]
    assert all(x['accessible'] is True for x in result['itinerary'])


@pytest.mark.parametrize('budget',[0,5,20,50,100,150])
def test_aggregate_budget(intent,budget):
    intent.budget=budget
    r=run(intent)[-1]
    assert sum(x['cost'] for x in r['itinerary'])<=budget
    assert r['budget']['known_group_total']==r['budget']['known_per_person']*intent.party_size


def test_ablation_and_stability(intent):
    a,b=run(intent)[-1],run(intent)[-1]
    assert a['comparison']['changed_positions']>0
    assert a['itinerary']==b['itinerary']
    assert a['comparison']['with_taste']!=a['comparison']['without_taste']
    assert all('Synthetic fixture' in c['explanation'] for c in a['itinerary'])


def test_request_construction_and_parsing():
    seen=[]
    def handle(request):
        seen.append(request)
        if request.url.path=='/search':
            return httpx.Response(200,json={'results':[{'entity_id':'real-id','name':'Radiohead','subtype':'urn:entity:artist'}]})
        return httpx.Response(200,json={'results':{'entities':[{'entity_id':'place-id','name':'Venue','subtype':'urn:entity:place','properties':{'websites':['javascript:alert(1)','https://example.com']},'query':{'affinity':.8}}]}})
    async def scenario():
        c=QlooClient('private-key','https://hackathon.api.qloo.com',httpx.MockTransport(handle))
        identifier=await c.resolve(Seed(name='Radiohead'))
        candidates=await c.discover([identifier],'Chicago')
        assert identifier=='real-id' and candidates[0].raw_query=={'affinity':.8}
        assert candidates[0].source_url=='https://example.com'
        assert candidates[0].cost is None and candidates[0].taste_score==1
    asyncio.run(scenario())
    assert seen[0].headers['X-Api-Key']=='private-key'
    assert seen[0].url.params['types']=='urn:entity:artist'
    assert seen[1].url.params['signal.interests.entities']=='real-id'
    assert seen[1].url.params['filter.location.radius']=='0'
    assert 'private-key' not in str(seen[0].url)


@pytest.mark.parametrize('status',[429,500])
def test_retry_bounded(status):
    async def scenario():
        delays=[]
        async def sleep(delay):delays.append(delay)
        c=QlooClient('key','https://api.qloo.com',httpx.MockTransport(lambda r:httpx.Response(status,headers={'Retry-After':'2'})),sleep)
        with pytest.raises(IntegrationError):await c.get('/search',{})
        assert c.calls==3 and len(delays)==2 and max(delays)<=4
    asyncio.run(scenario())


def test_timeout_and_auth_no_retry():
    async def scenario():
        async def sleep(_):pass
        def timeout(r):raise httpx.ReadTimeout('secret must not escape')
        c=QlooClient('key','https://api.qloo.com',httpx.MockTransport(timeout),sleep)
        with pytest.raises(IntegrationError,match='timed out'):await c.get('/search',{})
        assert c.calls==3
        c=QlooClient('key','https://api.qloo.com',httpx.MockTransport(lambda r:httpx.Response(401)),sleep)
        with pytest.raises(IntegrationError,match='401'):await c.get('/search',{})
        assert c.calls==1
    asyncio.run(scenario())


@pytest.mark.parametrize('payload',[{}, {'results':{}},{'results':[{'name':'bad'}]},{'success':False,'results':[]}])
def test_malformed_response(payload):
    with pytest.raises(IntegrationError):rows(payload)


@pytest.mark.parametrize('base',['http://api.qloo.com','https://evil.example','https://api.qloo.com@evil.example','https://api.qloo.com/path'])
def test_no_credential_exfiltration(base):
    with pytest.raises(IntegrationError):QlooClient('key',base)


def test_ambiguous_entity():
    async def scenario():
        entity={'name':'Radiohead','entity_id':'a','subtype':'urn:entity:artist'}
        c=QlooClient('key','https://api.qloo.com',httpx.MockTransport(lambda r:httpx.Response(200,json={'results':[entity,entity]})))
        assert await c.resolve(Seed(name='Radiohead')) is None
    asyncio.run(scenario())


def test_live_pipeline_keeps_unknown_facts_provisional(intent):
    def handler(request):
        entity={'name':'Japanese Breakfast','entity_id':'artist-id','subtype':'urn:entity:artist'}
        if request.url.path=='/search':return httpx.Response(200,json={'results':[entity]})
        return httpx.Response(200,json={'results':{'entities':[{'name':'Documented venue','entity_id':'venue-id','subtype':'urn:entity:place'}]}})
    client=QlooClient('key','https://api.qloo.com',httpx.MockTransport(handler))
    result=run(intent,client,'live')[-1]
    assert result['itinerary']==[] and result['budget']['complete'] is False
    assert result['alternatives'][0]['source']=='qloo'
    assert result['alternatives'][0]['cost'] is None
    assert 'unverified' in result['alternatives'][0]['warnings'][0]
    assert result['metrics']['qloo_calls']==3
    assert result['decisions'][0]['action']=='expand_discovery'


@pytest.mark.parametrize('invalid',[False,True])
def test_llm_structured_output_validation(intent,monkeypatch,invalid):
    from backend.app.llm import interpret_text
    from backend.app.models import TextRequest
    monkeypatch.setenv('OPENAI_API_KEY','mock-key')
    def handler(request):
        payload=json.loads(request.content)
        schema=payload['response_format']['json_schema']
        assert schema['strict'] and schema['schema']['additionalProperties'] is False
        assert payload['max_completion_tokens']==1500
        result=intent.model_dump(mode='json');result['budget']=-10 if invalid else 50
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(result)}}]})
    async def scenario():
        if invalid:
            with pytest.raises(IntegrationError):await interpret_text(TextRequest(text='Make it cheaper',current=intent),httpx.MockTransport(handler))
        else:
            result=await interpret_text(TextRequest(text='Make it cheaper',current=intent),httpx.MockTransport(handler))
            assert result.budget==50 and result.seeds==intent.seeds
    asyncio.run(scenario())
