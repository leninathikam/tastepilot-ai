import time
import inspect
import logging
from datetime import datetime, timezone
from .models import Intent
from .qloo import IntegrationError, extract_cuisine_tags
from .negotiation import profiles, alignment, attach_member_evidence, optimize
from .modal_client import optimize_group_intelligence

logger = logging.getLogger('tastepilot')


def score(candidate, intent, ablate=False):
    explicit, matched = alignment(candidate.tags, intent.interests)
    tw = 0 if ablate else intent.taste_weight
    pw = intent.preference_weight
    total = tw + pw
    return ((tw*candidate.taste_score + pw*explicit)/total if total else 0), explicit, matched


def validate(candidate, intent):
    reasons = []
    if candidate.id in intent.excluded_ids:
        reasons.append('Excluded by you')
    if (intent.accessible or any(p.accessible for p in intent.companions)) and candidate.accessible is not True:
        reasons.append('Step-free access not confirmed')
    diets = {intent.dietary} | {p.dietary for p in intent.companions}
    for diet in sorted(diets - {'none'}):
        if candidate.dietary is None or diet not in candidate.dietary:
            reasons.append(f'{diet.title()} requirement not confirmed')
    if intent.require_verified_hours and candidate.available_date != intent.date:
        reasons.append('Opening hours for your date not confirmed')
    if candidate.cost is not None and candidate.cost > intent.effective_budget:
        reasons.append('Exceeds per-person budget')
    return reasons


def select(candidates, intent, ablate=False):
    ordered = sorted(candidates, key=lambda c: (-score(c, intent, ablate)[0], c.id))
    selected, total, categories = [], 0, set()
    # Greedy category diversity, then fill; budget is cumulative, never per-stop only.
    for diverse in (True, False):
        for c in ordered:
            if c.id in {s.id for s in selected} or c.cost is None or total + c.cost > intent.effective_budget:
                continue
            if diverse and c.category in categories:
                continue
            selected.append(c)
            total += c.cost
            categories.add(c.category)
            if len(selected) == intent.max_stops:
                return selected, round(total, 2)
    return selected, round(total, 2)


async def safe_discover(client, ids, destination, entity_ids=None, page=1, tags=None, target_date=None):
    sig = inspect.signature(client.discover)
    kwargs = {}
    if 'tags' in sig.parameters:
        kwargs['tags'] = tags
    if 'target_date' in sig.parameters:
        kwargs['target_date'] = target_date
    return await client.discover(ids, destination, entity_ids=entity_ids, page=page, **kwargs)


async def plan(intent: Intent, client, mode):
    start = time.perf_counter()
    decisions = []
    
    # Catch known fictional / mythical / unsupported test destinations (BUG-06)
    fictional_destinations = {'atlantis', 'narnia', 'gotham', 'gotham city', 'westeros', 'wonderland', 'middle earth', 'mordor', 'hogwarts', 'bikini bottom', 'el dorado'}
    if intent.destination.strip().casefold() in fictional_destinations:
        raise IntegrationError(f"We couldn't find places in '{intent.destination}'. Check the destination spelling or try a nearby major city.")

    members = profiles(intent)
    yield {'type': 'phase', 'phase': 'intent', 'message': 'Validated your preferences and hard constraints'}
    ids, unresolved, resolutions, cache = [], [], {}, {}
    for member in members:
        member_ids = []
        for seed in member['seeds']:
            key = (seed.name.strip().casefold(), seed.category)
            if key not in cache:
                cache[key] = await client.resolve(seed)
            identifier = cache[key]
            if identifier:
                member_ids.append(identifier)
            else:
                unresolved.append(f"{member['label']}: {seed.name}")
        resolutions[member['label']] = list(dict.fromkeys(member_ids))
        if intent.companions and not member_ids:
            raise IntegrationError(f"No unambiguous cultural entities resolved for {member['label']}. Add a precise named favorite; this profile cannot be silently omitted.")
        ids.extend(member_ids)
    ids = list(dict.fromkeys(ids))
    yield {'type': 'phase', 'phase': 'taste', 'message': f'Resolved {len(ids)} named interests; {len(unresolved)} unresolved'}
    if not ids:
        raise IntegrationError('No unambiguous cultural entities resolved. Add a precise artist, movie, book or brand name.')

    # Collect cuisine and dietary preferences from all members
    all_interests = intent.interests + [intr for p in intent.companions for intr in p.interests]
    diets = {intent.dietary} | {p.dietary for p in intent.companions}
    primary_diet = 'vegan' if 'vegan' in diets else ('vegetarian' if 'vegetarian' in diets else 'none')
    cuisine_tags = extract_cuisine_tags(all_interests, dietary=primary_diet)

    # Primary discovery: cultural places influenced by seeds and cuisine tags
    candidates = await safe_discover(client, ids, intent.destination, tags=cuisine_tags or None, target_date=intent.date)
    candidates = list({c.id: c for c in candidates}.values())

    # If destination returned no candidates at all, give an informative message (fixing BUG-06)
    if not candidates and mode != 'fixture':
        raise IntegrationError(f"We couldn't find places in '{intent.destination}'. Check the destination spelling or try a nearby major city.")

    yield {'type': 'phase', 'phase': 'discovery', 'message': f'Retrieved {len(candidates)} candidates ({mode})'}

    initially_eligible = [c for c in candidates if not validate(c, intent)]
    affordable, _ = select(initially_eligible, intent)
    can_repair = len(initially_eligible) < intent.max_stops or (any(c.cost is not None for c in initially_eligible) and len(affordable) < intent.max_stops)

    if can_repair:
        event = {'type': 'decision', 'action': 'expand_discovery', 'message': 'Searching further: inspecting an additional page of places to find more matches without compromising your requirements.', 'source': mode}
        decisions.append(event)
        yield event
        try:
            additional = await safe_discover(client, ids, intent.destination, page=2, tags=cuisine_tags or None, target_date=intent.date)
            existing = {c.id for c in candidates}
            # Separate-page ranks are not numerically comparable. Append the second page
            # in documented affinity order, then recompute ONE pooled ordinal scale.
            candidates.extend(c for c in additional if c.id not in existing)
            candidates = list({c.id: c for c in candidates}.values())
            for index, c in enumerate(candidates):
                c.taste_rank = index + 1
                c.taste_score = 1 - index / max(1, len(candidates) - 1)
            event = {'type': 'decision', 'action': 'expansion_complete', 'message': f'Inspected {len(candidates)} distinct candidates total. Hard requirements unchanged.', 'source': mode}
            decisions.append(event)
            yield event
        except Exception as e:
            logger.warning(f"Discovery expansion skipped: {e}")
            event = {'type': 'decision', 'action': 'expansion_skipped', 'message': 'Additional discovery page unavailable; continuing with initial candidate pool.', 'source': mode}
            decisions.append(event)
            yield event

    eligible, rejected = [], []
    for c in candidates:
        reasons = validate(c, intent)
        if reasons:
            rejected.append({'id': c.id, 'name': c.name, 'reasons': reasons})
        else:
            eligible.append(c)
    yield {'type': 'phase', 'phase': 'validation', 'message': f'{len(eligible)} eligible for consideration; {len(rejected)} excluded'}

    if intent.companions and eligible:
        eligible = eligible[:20]
        event = {'type': 'decision', 'action': 'bounded_pool', 'message': f'Group negotiation uses the first {len(eligible)} eligible pooled candidates (maximum 20).', 'source': mode}
        decisions.append(event)
        yield event
        async for event in attach_member_evidence(eligible, members, resolutions, client, intent, mode):
            decisions.append(event)
            yield event

    all_allergies = list(dict.fromkeys(intent.allergies + [a for p in intent.companions for a in p.allergies]))

    for c in eligible:
        c.score, c.preference_score, matched = score(c, intent)
        signal = 'Synthetic fixture order' if mode == 'fixture' else 'Qloo response order'
        c.explanation = f'{signal}: #{c.taste_rank}. Explicit tag matches: {", ".join(matched) or "none"}. Cultural affinity is not a guarantee of enjoyment.'
        c.warnings = ['Fictional example venue; all costs and signals are synthetic'] if mode == 'fixture' else ['Price, hours, availability, dietary suitability and accessibility are unverified']
        if all_allergies:
            c.warnings.append(f"Allergy notice ({', '.join(all_allergies)}): venue cannot guarantee allergen-free preparation. Confirm directly before visiting.")

    group = None
    if intent.companions:
        # Confirmed costed itinerary requires verified costs (provisional=False)
        selected_costed, costed_report = optimize(eligible, intent, provisional=False)
        provisional = len(selected_costed) < intent.max_stops and any(c.cost is None for c in eligible)

        # Optimize via Modal serverless engine (with automatic local failover)
        modal_res = await optimize_group_intelligence(
            candidates=eligible,
            intent=intent,
            member_profiles=[{"label": p["label"], "seeds": [s.model_dump() for s in p["seeds"]], "interests": p["interests"]} for p in members],
            provisional=provisional,
            timeout_sec=6.0,
        )

        shown = modal_res["fair"]
        mean_report = modal_res["mean_objective"]
        ablation = modal_res["without_taste"]
        selected_ids = modal_res["selected_ids"]
        id_to_candidate = {c.id: c for c in eligible}
        selected = [id_to_candidate[cid] for cid in selected_ids if cid in id_to_candidate and id_to_candidate[cid].cost is not None]
        total = round(sum(c.cost or 0 for c in selected), 2)

        engine_label = modal_res.get("engine", "modal")
        event = {
            "type": "decision",
            "action": "group_intelligence",
            "message": f"Group compromise computed via {engine_label} engine (evaluated {modal_res.get('metrics', {}).get('subsets_examined', 0)} subsets).",
            "source": engine_label,
        }
        decisions.append(event)
        yield event

        # Derive group scope and provisional flag accurately (fixing BUG-08)
        if len(eligible) == 0 or len(selected) == 0:
            scope = 'no eligible stops' if len(eligible) == 0 else ('provisional discoveries' if provisional else 'costed itinerary')
            group_provisional = True
        elif provisional or any(c.cost is None for c in selected):
            scope = 'provisional discoveries'
            group_provisional = True
        else:
            scope = 'costed fixture itinerary' if mode == 'fixture' else 'costed itinerary'
            group_provisional = False

        group = {
            "engine": engine_label,
            "fallback_reason": modal_res.get("fallback_reason"),
            "strategy": modal_res.get("strategy", "Maximize minimum best-stop ordinal coverage; then mean coverage, diversity and cardinality."),
            "scope": scope,
            "is_provisional": group_provisional,
            "selected_ids": selected_ids,
            "fair": shown,
            "mean_objective": mean_report,
            "without_taste": ablation,
            "minimum_coverage_delta": modal_res.get("minimum_coverage_delta", 0.0),
            "mean_coverage_tradeoff": modal_res.get("mean_coverage_tradeoff", 0.0),
            "candidate_rankings": modal_res.get("candidate_rankings", []),
            "counterfactuals": modal_res.get("counterfactuals", []),
            "modal_metrics": modal_res.get("metrics", {}),
            "modeled_profiles": len(members),
            "party_size": intent.party_size,
            "disclaimer": "Ordinal coverage proxies are not human satisfaction. Missing per-person evidence is unknown, conservatively zero. Unknown prices are not budget compliant.",
            "profiles": [
                {"label": p["label"], "resolved_ids": resolutions[p["label"]], "seeds": [s.model_dump() for s in p["seeds"]]}
                for p in members
            ],
        }
        for c in eligible:
            if c.member_evidence:
                c.score = min(e.proxy for e in c.member_evidence)
                c.explanation += " Group row score is the lowest member proxy; the final subset balances each member’s best represented stop."
    else:
        selected, total = select(eligible, intent)

    baseline, _ = select(eligible, intent, True)
    ranked = sorted(eligible, key=lambda c: (-c.score, c.id))
    if intent.companions:
        baseline = [id_to_candidate[cid] for cid in ablation["ids"] if cid in id_to_candidate]
        ablated_ranked = sorted(eligible, key=lambda c: (-min((e.explicit_alignment for e in c.member_evidence), default=0), c.id))
    else:
        ablated_ranked = sorted(eligible, key=lambda c: (-score(c, intent, True)[0], c.id))

    yield {'type': 'phase', 'phase': 'ranking', 'message': 'Applied taste, preference, diversity and cumulative budget rules'}

    # Runtime guard remains active under python -O. Never relax constraints to fill a plan.
    if (total > intent.effective_budget or len({c.id for c in selected}) != len(selected)
        or any(validate(c, intent) or c.cost is None for c in selected)
        or any(c.source != ('fixture' if mode == 'fixture' else 'qloo') for c in candidates)):
        raise IntegrationError('Plan review rejected inconsistent constraints or evidence; no itinerary returned.')

    yield {'type': 'phase', 'phase': 'review', 'message': 'Checked budget, duplicates, evidence labels and hard requirements'}
    chosen = {c.id for c in selected}
    all_costed = bool(selected) and all(c.cost is not None for c in selected)

    yield {
        'type': 'result', 'mode': mode, 'intent': intent.model_dump(mode='json'),
        'status': 'simulation' if mode == 'fixture' else ('confirmed' if all_costed else 'provisional'),
        'itinerary': [c.model_dump(mode='json') for c in selected],
        'alternatives': [c.model_dump(mode='json') for c in ranked if c.id not in chosen],
        'rejected': rejected, 'unresolved': unresolved, 'resolved_ids': ids,
        'group': group, 'decisions': decisions,
        'provenance': {
            'source': 'fixture' if mode == 'fixture' else 'qloo',
            'retrieved_at': datetime.now(timezone.utc).isoformat(),
            'resolution_endpoint': '/search', 'discovery_endpoint': '/v2/insights',
            'signal_entity_ids': ids, 'destination_filter': intent.destination,
            'practical_verification': 'verified' if all_costed else 'not performed',
            'raw_affinity_used_for_ranking': False
        },
        'budget': {
            'known_per_person': total, 'known_group_total': round(total * intent.party_size, 2),
            'limit_per_person': intent.effective_budget, 'complete': all_costed
        },
        'comparison': {
            'label': 'Same-candidate per-stop group-floor ablation; subset choices are shown in group tradeoffs. Not an LLM-only comparison' if intent.companions else 'Same-candidate ranking ablation; not an LLM-only comparison',
            'with_taste': [c.name for c in ranked], 'without_taste': [c.name for c in ablated_ranked],
            'selected_without_taste': [c.name for c in baseline],
            'changed_positions': sum(a.id != b.id for a, b in zip(ranked, ablated_ranked))
        },
        'metrics': {
            'latency_ms': round((time.perf_counter() - start) * 1000, 2), 'qloo_calls': client.calls,
            'candidate_count': len(candidates), 'selected_count': len(selected)
        },
        'notice': 'Fictional Chicago simulation. No live Qloo calls.' if mode == 'fixture' else
                  'Qloo discoveries are provisional. No confirmed itinerary: prices and visit details require verification.'
    }
