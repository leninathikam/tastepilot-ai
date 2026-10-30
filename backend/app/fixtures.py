from .models import Candidate

# Authored test data. These venues and signals are fictional, not API recordings.
DATA = [
    ('Paper Lantern Kitchen', 'dining', ['Korean food', 'vegetarian'], 32, True),
    ('Side B Listening Room', 'music', ['indie music', 'vinyl'], 28, True),
    ('Open Frame Gallery', 'art', ['contemporary art', 'independent art'], 12, True),
    ('City Lights Dining Hall', 'dining', ['Korean food', 'indie music', 'contemporary art'], 65, False),
    ('Pocket Park Sketch Walk', 'art', ['contemporary art', 'outdoors'], 0, True),
    ('Small Hours Records', 'music', ['indie music', 'vinyl'], 8, True),
]


class FixtureClient:
    calls = 0

    async def resolve(self, seed):
        known = {'artist': {'japanese breakfast', 'radiohead', 'khruangbin'}, 'movie': {'past lives'}, 'book': {'dune'}, 'brand': {'uniqlo'}}
        return 'fixture:' + seed.name.lower() if seed.name.lower() in known.get(seed.category, set()) else None

    async def discover(self, ids, destination, entity_ids=None, page=1, *args, **kwargs):
        if destination.casefold().strip() != 'chicago' or page > 1:
            return []
        # Explicitly synthetic preference-specific orderings; never Qloo recordings.
        orders={'japanese breakfast':[0,1,2,3,4,5], 'radiohead':[1,5,4,2,0,3],
                'khruangbin':[5,1,0,4,2,3], 'past lives':[2,4,0,3,1,5],
                'dune':[4,2,5,1,0,3], 'uniqlo':[3,0,5,2,4,1]}
        signals=[orders[x.removeprefix('fixture:')] for x in ids if x.removeprefix('fixture:') in orders]
        if not signals:
            return []
        order=sorted(range(len(DATA)),key=lambda i:(sum(o.index(i) for o in signals),i))
        if entity_ids is not None:
            order=[i for i in order if f'fixture:{i}' in entity_ids]
        return [Candidate(id=f'fixture:{i}', name=DATA[i][0], category=DATA[i][1], tags=DATA[i][2], source='fixture',
                          taste_rank=rank+1, taste_score=1-rank/max(1,len(order)-1), cost=DATA[i][3],
                          accessible=DATA[i][4], dietary=['vegetarian'] if DATA[i][1] == 'dining' else ['vegetarian', 'vegan'])
                for rank,i in enumerate(order)]

    async def search_places(self, query: str, *args, **kwargs):
        return []
