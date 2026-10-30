import asyncio
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
import httpx
from .models import Candidate, Seed


class IntegrationError(Exception):
    pass


def has_type(entity, expected):
    # Search returns types; some Insights versions also expose subtype.
    types = entity.get('types')
    return entity.get('subtype') == expected or (isinstance(types, list) and expected in types)


def rows(payload, search=False):
    if not isinstance(payload, dict) or payload.get('success') is False:
        raise IntegrationError('Qloo returned an unsuccessful or malformed response')
    result = payload.get('results')
    if isinstance(result, dict):
        result = result.get('entities')
    if not isinstance(result, list):
        raise IntegrationError('Qloo response did not contain an entity list')
    if any(not isinstance(x, dict) or not isinstance(x.get('entity_id'), str)
           or not isinstance(x.get('name'), str) for x in result):
        raise IntegrationError('Qloo returned malformed entity records')
    return result


class QlooClient:
    def __init__(self, key, base, transport=None, sleep=asyncio.sleep):
        parsed = urlparse(base)
        if parsed.scheme != 'https' or parsed.hostname not in {
            'api.qloo.com', 'hackathon.api.qloo.com', 'staging.api.qloo.com'
        } or parsed.username or parsed.password or parsed.port or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
            raise IntegrationError('Qloo base URL must be an approved HTTPS origin')
        if not key or key.startswith('replace_'):
            raise IntegrationError('Configure QLOO_API_KEY before enabling live mode')
        self.key, self.base, self.transport, self.sleep = key, base.rstrip('/'), transport, sleep
        self.calls = 0

    async def get(self, path, params):
        async with httpx.AsyncClient(timeout=12, transport=self.transport, follow_redirects=False) as client:
            for attempt in range(3):
                self.calls += 1
                try:
                    r = await client.get(self.base + path, params=params, headers={'X-Api-Key': self.key})
                    if r.status_code == 404:
                        return {'results': []}
                    if r.status_code == 429 or r.status_code >= 500:
                        if attempt < 2:
                            retry = r.headers.get('Retry-After', '')
                            delay = .5 * 2**attempt
                            if retry:
                                try:
                                    delay = max(0, float(retry))
                                except ValueError:
                                    try:
                                        delay = max(0, (parsedate_to_datetime(retry)-datetime.now(timezone.utc)).total_seconds())
                                    except (ValueError, TypeError):
                                        pass
                            if delay > 4:
                                raise IntegrationError('Qloo asked for a longer retry delay. Please retry later; no early retry was sent.')
                            await self.sleep(delay)
                            continue
                        raise IntegrationError('Qloo temporarily unavailable or rate limited; try again later')
                    if r.status_code != 200:
                        raise IntegrationError(f'Qloo request rejected (HTTP {r.status_code}); check access and configuration')
                    try:
                        return r.json()
                    except ValueError:
                        raise IntegrationError('Qloo returned invalid JSON') from None
                except (httpx.TimeoutException, httpx.NetworkError):
                    if attempt == 2:
                        raise IntegrationError('Qloo connection timed out or failed') from None
                    await self.sleep(.5 * 2**attempt)

    async def resolve(self, seed: Seed):
        entities = rows(await self.get('/search', {'query': seed.name, 'types': f'urn:entity:{seed.category}', 'take': 5}), True)
        exact = [x for x in entities if x['name'].casefold() == seed.name.strip().casefold()
                 and has_type(x, f'urn:entity:{seed.category}')]
        return exact[0]['entity_id'] if len(exact) == 1 else None

    async def discover(self, ids, destination, entity_ids=None, page=1):
        params = {
            'filter.type': 'urn:entity:place', 'signal.interests.entities': ','.join(ids),
            'filter.location.query': destination, 'filter.location.radius': 0, 'take': 20, 'page': page,
        }
        if entity_ids is not None:
            if not entity_ids:
                return []
            params['filter.results.entities'] = ','.join(entity_ids)
        entities = rows(await self.get('/v2/insights', params))
        candidates = []
        for i, entity in enumerate(entities):
            if not has_type(entity, 'urn:entity:place'):
                continue
            props = entity.get('properties') or {}
            if not isinstance(props, dict):
                raise IntegrationError('Qloo returned malformed place properties')
            websites = props.get('websites') or []
            website = next((u for u in websites if isinstance(u, str) and urlparse(u).scheme in ('http','https')), None)
            candidates.append(Candidate(
                id=entity['entity_id'], name=entity['name'], source='qloo', source_url=website,
                address=props.get('address') if isinstance(props.get('address'), str) else None,
                tags=[t['name'] for t in entity.get('tags', []) if isinstance(t, dict) and isinstance(t.get('name'), str)],
                taste_rank=i+1, taste_score=1-i/max(1,len(entities)-1), raw_query=entity.get('query') if isinstance(entity.get('query'),dict) else {},
            ))
        return candidates
