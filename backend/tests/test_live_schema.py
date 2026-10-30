import asyncio
import httpx
from backend.app.models import Seed
from backend.app.qloo import QlooClient, has_type


def test_search_and_insights_accept_observed_types_array():
    def handler(request):
        if request.url.path == '/search':
            return httpx.Response(200,json={'results':[{'entity_id':'artist-id','name':'Radiohead','types':['urn:entity:artist']}]})
        return httpx.Response(200,json={'results':{'entities':[{'entity_id':'place-id','name':'Example place','types':['urn:entity:place']}]}})
    async def run():
        client=QlooClient('test','https://hackathon.api.qloo.com',transport=httpx.MockTransport(handler))
        assert await client.resolve(Seed(name='Radiohead')) == 'artist-id'
        places=await client.discover(['artist-id'],'Chicago')
        assert len(places)==1 and places[0].id=='place-id'
    asyncio.run(run())


def test_type_check_rejects_wrong_or_malformed_types():
    assert not has_type({'types':'urn:entity:artist'},'urn:entity:artist')
    assert not has_type({'types':['urn:entity:movie']},'urn:entity:artist')
