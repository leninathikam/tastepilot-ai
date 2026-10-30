# API contract and limits

Authentication: X-Api-Key header, server-side only. Configurable HTTPS base restricted to api.qloo.com, staging.api.qloo.com or hackathon.api.qloo.com. Hackathon base was validated with the issued key on October 30.

- GET /search: query, types (entity URN), take. Resolve exact names; reject ambiguous/missing results.
- GET /v2/insights: filter.type=urn:entity:place, signal.interests.entities=comma-separated IDs, filter.location.query, filter.location.radius=0, take=20. Radius zero restricts to locality boundaries per official parameters.md.
- GET /v2/tags is documented but not needed by initial named-entity workflow.
- Insights response: results.entities; entity_id, name, types (or subtype), properties, tags. Preserve returned query metadata rather than inventing an affinity field. Ranking uses documented affinity-sorted response order as a within-query ordinal signal, not a probability or personal satisfaction score.
- Search response parsing accepts results list or results.entities, with strict row validation. Live envelope verified: search uses the types array. Scoped filter.results.entities also passed a live smoke test.

Supported documented categories include artist, book, brand, destination, movie, person, place, podcast, TV show and video game. UI enables artist/movie/book/brand as seeds, place as output.

Insights take max 50 per documentation; application requests 20. Event numeric quotas, expiration and retention permission not published in inspected kit. 429 is documented. Three attempts maximum, bounded backoff, timeouts, no automatic fixture substitution in live mode. No durable raw Qloo response caching or public response corpus until licensing is established.

Sources: https://github.com/qloo/docs-public/tree/main/reference and https://github.com/qloo/qloo-hackathon-kit/blob/main/docs/API_ACCESS.md.
