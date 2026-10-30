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


CUISINE_MAP = {
    'korean': 'urn:tag:cuisine:qloo:korean',
    'italian': 'urn:tag:cuisine:qloo:italian',
    'japanese': 'urn:tag:cuisine:qloo:japanese',
    'chinese': 'urn:tag:cuisine:qloo:chinese',
    'mexican': 'urn:tag:cuisine:qloo:mexican',
    'american': 'urn:tag:cuisine:qloo:american',
    'thai': 'urn:tag:cuisine:qloo:thai',
    'indian': 'urn:tag:cuisine:qloo:indian',
    'french': 'urn:tag:cuisine:qloo:french',
    'vietnamese': 'urn:tag:cuisine:qloo:vietnamese',
    'spanish': 'urn:tag:cuisine:qloo:spanish',
    'mediterranean': 'urn:tag:cuisine:qloo:mediterranean',
    'asian': 'urn:tag:cuisine:qloo:asian',
    'barbecue': 'urn:tag:cuisine:qloo:american',
    'bbq': 'urn:tag:cuisine:qloo:american',
    'pizza': 'urn:tag:cuisine:qloo:italian',
}


def extract_cuisine_tags(interests: list[str], dietary: str = 'none') -> list[str]:
    tags = []
    for interest in interests:
        cleaned = interest.casefold().strip()
        for key, urn in CUISINE_MAP.items():
            if key in cleaned and urn not in tags:
                tags.append(urn)
    if dietary == 'vegetarian' and 'urn:tag:dietary:place:vegetarian_friendly' not in tags:
        tags.append('urn:tag:dietary:place:vegetarian_friendly')
    elif dietary == 'vegan':
        if 'urn:tag:dietary:place:vegan_options' not in tags:
            tags.append('urn:tag:dietary:place:vegan_options')
        if 'urn:tag:dietary:place:vegetarian_friendly' not in tags:
            tags.append('urn:tag:dietary:place:vegetarian_friendly')
    return tags


def _enrich_candidate(entity, index, total, target_date=None) -> Candidate:
    props = entity.get('properties') or {}
    if not isinstance(props, dict):
        raise IntegrationError('Qloo returned malformed place properties')
    websites = props.get('websites') or []
    website = next((u for u in websites if isinstance(u, str) and urlparse(u).scheme in ('http', 'https')), None)

    raw_tags = entity.get('tags') or []
    tag_names = list(dict.fromkeys(t['name'] for t in raw_tags if isinstance(t, dict) and isinstance(t.get('name'), str)))
    tag_names_lower = {t.casefold() for t in tag_names}

    # Step-free accessibility from tags and descriptions
    accessible = None
    amenities_desc = (props.get('amenities_description') or '').casefold()
    if (any('wheelchair accessible' in t or 'elevator' in t for t in tag_names_lower)
            or 'wheelchair accessible' in amenities_desc
            or 'fully accessible' in amenities_desc):
        accessible = True

    # Dietary suitability from tags
    dietary = []
    is_veg = any('vegetarian' in t for t in tag_names_lower)
    is_vegan = any('vegan' in t for t in tag_names_lower)
    if is_vegan:
        dietary.extend(['vegan', 'vegetarian'])
    elif is_veg:
        dietary.append('vegetarian')
    dietary = list(dict.fromkeys(dietary)) or None

    # Hours and date availability
    hours = props.get('hours') if isinstance(props.get('hours'), dict) else None
    available_date = None
    if hours and target_date:
        day_name = target_date.strftime('%A').lower()
        day_hours = hours.get(day_name)
        if isinstance(day_hours, list) and day_hours:
            first_period = day_hours[0]
            if isinstance(first_period, dict) and not first_period.get('closed', False):
                available_date = target_date

    # Cost: strictly never invent prices. Only verify if explicit free admission or public municipal amenities.
    cost = None
    cost_desc = (props.get('cost_description') or '').casefold()
    is_free = (
        'free' in cost_desc
        or any(
            phrase in t
            for t in tag_names_lower
            for phrase in (
                'free admission', 'has free admission', 'free entry', 'free of charge',
                'no admission fee', 'no cover', 'free to the public', 'admission is free', 'free public'
            )
        )
        or any(t in ('public park', 'public parks', 'public plaza', 'pedestrian path', 'public space', 'public beach', 'public promenade') for t in tag_names_lower)
    )
    if is_free:
        cost = 0.0

    price_level = props.get('price_level') if isinstance(props.get('price_level'), int) else None

    # Category and dining identification
    is_dining = (
        any(t in tag_names_lower for t in ('restaurant', 'dining drinking', 'cafe', 'bakery', 'bistro', 'food', 'casual dining', 'fine dining'))
        or any('restaurant' in t for t in tag_names_lower)
    )
    category = 'dining' if is_dining else 'place'

    return Candidate(
        id=entity['entity_id'], name=entity['name'], category=category, source='qloo', source_url=website,
        address=props.get('address') if isinstance(props.get('address'), str) else None,
        tags=tag_names,
        taste_rank=index + 1, taste_score=1 - index / max(1, total - 1),
        raw_query=entity.get('query') if isinstance(entity.get('query'), dict) else {},
        cost=cost, accessible=accessible, dietary=dietary, available_date=available_date,
        hours=hours, price_level=price_level, is_dining=is_dining,
    )


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
        async with httpx.AsyncClient(timeout=18, transport=self.transport, follow_redirects=False) as client:
            for attempt in range(3):
                self.calls += 1
                try:
                    r = await client.get(self.base + path, params=params, headers={'X-Api-Key': self.key})
                    if r.status_code == 404:
                        return {'results': []}
                    if r.status_code == 400:
                        try:
                            err_data = r.json()
                            errors = err_data.get('errors') or []
                            for e in errors:
                                if 'filter.location' in str(e.get('path', '')):
                                    dest = params.get('filter.location.query', 'that destination')
                                    raise IntegrationError(f"We couldn't find places in '{dest}'. Check the destination spelling or try a nearby major city.")
                        except (ValueError, TypeError):
                            pass
                        raise IntegrationError(f'Qloo request rejected (HTTP {r.status_code}); check access and configuration')
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

    def _normalize_destination(self, destination: str):
        dest_clean = destination.strip()
        radius = 0
        if dest_clean.casefold() in ('new york', 'new york, ny', 'nyc', 'ny'):
            dest_clean = 'New York City'
            radius = 35000
        return dest_clean, radius

    async def discover(self, ids, destination, entity_ids=None, page=1, tags=None, target_date=None):
        dest_clean, radius = self._normalize_destination(destination)
        params = {
            'filter.type': 'urn:entity:place',
            'filter.location.query': dest_clean,
            'filter.location.radius': radius,
            'take': 20,
            'page': page,
        }
        if ids:
            params['signal.interests.entities'] = ','.join(ids)
        if tags:
            params['signal.interests.tags'] = ','.join(tags)
        if entity_ids is not None:
            if not entity_ids:
                return []
            params['filter.results.entities'] = ','.join(entity_ids)

        entities = rows(await self.get('/v2/insights', params))
        candidates = []
        for i, entity in enumerate(entities):
            if not has_type(entity, 'urn:entity:place'):
                continue
            candidates.append(_enrich_candidate(entity, i, len(entities), target_date=target_date))
        return candidates

    async def search_places(self, query: str, take: int = 10, target_date=None) -> list[Candidate]:
        entities = rows(await self.get('/search', {'query': query, 'types': 'urn:entity:place', 'take': take}), True)
        candidates = []
        for i, entity in enumerate(entities):
            if not has_type(entity, 'urn:entity:place'):
                continue
            candidates.append(_enrich_candidate(entity, i, len(entities), target_date=target_date))
        return candidates
