import asyncio
import json
import httpx
import pytest
from pydantic import ValidationError
from backend.app.models import Intent, Seed, Companion, Candidate, MemberEvidence
from backend.app.fixtures import FixtureClient
from backend.app.qloo import QlooClient, IntegrationError
from backend.app.planner import plan, validate
from backend.app.negotiation import optimize, alignment


def group(**updates):
    data=dict(date='2026-10-31',seeds=[Seed(name='Japanese Breakfast')],interests=['Korean food'],
              companions=[Companion(label='Friend',seeds=[Seed(name='Radiohead')])])
    data.update(updates)
    return Intent(**data)


def run(intent,client=None,mode='fixture'):
    async def collect():return [e async for e in plan(intent,client or FixtureClient(),mode)]
    return asyncio.run(collect())


def test_group_different_evidence_and_preserved_constraints():
    intent=group()
    result=run(intent)[-1]
    assert result['group']['modeled_profiles']==2
    assert result['group']['fair']['minimum_coverage']>=result['group']['mean_objective']['minimum_coverage']
    c=(result['itinerary']+result['alternatives'])[0]
    assert len(c['member_evidence'])==2
    assert c['member_evidence'][0]['returned_rank']!=c['member_evidence'][1]['returned_rank']
    intent.budget=20;intent.excluded_ids=[c['id']]
    revised=run(intent)[-1]
    assert revised['budget']['known_per_person']<=20
    assert c['id'] not in [x['id'] for x in revised['itinerary']]
    assert revised['intent']['companions']==result['intent']['companions']


def test_companion_constraints_and_budget_are_shared():
    intent=group(companions=[Companion(label='Guest',seeds=[Seed(name='Radiohead')],budget=12,accessible=True,dietary='vegan')])
    result=run(intent)[-1]
    assert result['budget']['limit_per_person']==12
    assert result['budget']['known_per_person']<=12
    assert all(x['accessible'] is True and 'vegan' in x['dietary'] for x in result['itinerary'])
    assert any('Vegan requirement not confirmed' in x['reasons'] for x in result['rejected'])


def test_unknown_group_member_is_not_silently_dropped():
    with pytest.raises(IntegrationError,match='Friend'):
        run(group(companions=[Companion(label='Friend',seeds=[Seed(name='unknown')])]))


@pytest.mark.parametrize('update',[
    {'party_size':1},
    {'companions':[{'label':'You','seeds':[{'name':'Radiohead'}]}]},
    {'companions':[{'label':'A','seeds':[{'name':'Radiohead'}]},{'label':'a','seeds':[{'name':'Radiohead'}]}]},
])
def test_invalid_group_profiles(update):
    with pytest.raises(ValidationError):group(**update)


def test_exact_interest_matching_not_substrings():
    assert alignment(['party','art gallery'],['art'])[0]==0
    assert alignment(['art'],['ART','art'])[0]==1


def test_max_min_prefers_compromise_over_average():
    intent=group(max_stops=1,budget=50)
    def candidate(id,values):
        return Candidate(id=id,name=id,source='fixture',taste_rank=1,taste_score=1,cost=10,
                         member_evidence=[MemberEvidence(label=label,source='fixture',resolved_ids=['synthetic'],returned_rank=1,
                           ordinal_signal=value,explicit_alignment=0,matched_interests=[],proxy=value,note='Synthetic test case')
                           for label,value in zip(['You','Friend'],values)])
    candidates=[candidate('favorite',[1,.3]),candidate('compromise',[.6,.6])]
    fair,f=optimize(candidates,intent)
    average,a=optimize(candidates,intent,objective='mean')
    assert fair[0].id=='compromise' and average[0].id=='favorite'
    assert f['minimum_coverage']==.6 and a['minimum_coverage']==.3
    assert f['mean_coverage']<a['mean_coverage']


def test_tool_policy_expands_once_without_relaxing_requirements():
    class PagedClient(FixtureClient):
        def __init__(self):self.pages=[]
        async def discover(self,ids,destination,entity_ids=None,page=1):
            self.pages.append(page)
            return [Candidate(id=str(page),name=f'Place {page}',source='fixture',taste_rank=1,taste_score=1,cost=5,accessible=page==2)]
    client=PagedClient()
    result=run(Intent(date='2026-10-31',seeds=[Seed(name='Radiohead')],accessible=True,max_stops=1),client)[-1]
    assert client.pages==[1,2]
    assert [x['id'] for x in result['itinerary']]==['2']
    assert result['intent']['accessible'] is True
    assert [d['action'] for d in result['decisions']]==['expand_discovery','expansion_complete']


def test_request_scoping_and_missing_member_evidence_in_live_mock():
    seen=[]
    def handler(request):
        seen.append(request)
        params=request.url.params
        if request.url.path=='/search':
            name=params['query']
            return httpx.Response(200,json={'results':[{'name':name,'entity_id':'radio' if name=='Radiohead' else 'breakfast','subtype':'urn:entity:artist'}]})
        entities=[{'entity_id':f'p{i}','name':f'Place {i}','subtype':'urn:entity:place'} for i in range(3)]
        if 'filter.results.entities' in params and params['signal.interests.entities']=='radio':
            entities=entities[1:][::-1]
        return httpx.Response(200,json={'results':{'entities':entities}})
    result=run(group(),QlooClient('key','https://api.qloo.com',httpx.MockTransport(handler)),'live')[-1]
    rescoring=[r for r in seen if 'filter.results.entities' in r.url.params]
    assert len(rescoring)==2
    assert rescoring[0].url.params['filter.results.entities']==rescoring[1].url.params['filter.results.entities']
    assert all('Friend' not in str(r.url) and 'You' not in str(r.url) for r in seen)
    assert result['itinerary']==[] and result['group']['is_provisional'] is True
    p0=next(c for c in result['alternatives'] if c['id']=='p0')
    missing=next(e for e in p0['member_evidence'] if e['label']=='Friend')
    assert missing['ordinal_signal'] is None and 'unknown' in missing['note']
    assert result['budget']['complete'] is False
    assert result['group']['fair']['unknown_cost_count']>0


def test_fixture_order_depends_on_named_signal():
    a=run(Intent(date='2026-10-31',seeds=[Seed(name='Japanese Breakfast')]))[-1]
    b=run(Intent(date='2026-10-31',seeds=[Seed(name='Radiohead')]))[-1]
    assert a['comparison']['with_taste']!=b['comparison']['with_taste']


def test_long_retry_after_never_retried_early():
    async def scenario():
        delays=[]
        async def sleep(delay):delays.append(delay)
        client=QlooClient('key','https://api.qloo.com',httpx.MockTransport(lambda r:httpx.Response(429,headers={'Retry-After':'99'})),sleep)
        with pytest.raises(IntegrationError,match='no early retry'):await client.get('/search',{})
        assert client.calls==1 and delays==[]
    asyncio.run(scenario())


def test_source_mismatch_fails_runtime_review():
    class BadClient(FixtureClient):
        async def discover(self,*args,**kwargs):
            rows=await super().discover(*args,**kwargs)
            for row in rows:row.source='qloo'
            return rows
    with pytest.raises(IntegrationError,match='review rejected'):
        run(Intent(date='2026-10-31',seeds=[Seed(name='Radiohead')]),BadClient())
