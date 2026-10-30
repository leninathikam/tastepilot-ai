import time
from datetime import datetime, timezone
from .models import Intent
from .qloo import IntegrationError
from .negotiation import profiles, alignment, attach_member_evidence, optimize


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
    diets={intent.dietary}|{p.dietary for p in intent.companions}
    for diet in sorted(diets-{'none'}):
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
            if c.id in {s.id for s in selected} or c.cost is None or total+c.cost > intent.effective_budget:
                continue
            if diverse and c.category in categories:
                continue
            selected.append(c)
            total += c.cost
            categories.add(c.category)
            if len(selected) == intent.max_stops:
                return selected, round(total, 2)
    return selected, round(total, 2)


async def plan(intent: Intent, client, mode):
    start = time.perf_counter()
    decisions=[]
    members=profiles(intent)
    yield {'type': 'phase', 'phase': 'intent', 'message': 'Validated your preferences and hard constraints'}
    ids, unresolved, resolutions, cache = [], [], {}, {}
    for member in members:
        member_ids=[]
        for seed in member['seeds']:
            key=(seed.name.strip().casefold(),seed.category)
            if key not in cache:
                cache[key]=await client.resolve(seed)
            identifier=cache[key]
            if identifier:
                member_ids.append(identifier)
            else:
                unresolved.append(f"{member['label']}: {seed.name}")
        resolutions[member['label']]=list(dict.fromkeys(member_ids))
        if intent.companions and not member_ids:
            raise IntegrationError(f"No unambiguous cultural entities resolved for {member['label']}. Add a precise named favorite; this profile cannot be silently omitted.")
        ids.extend(member_ids)
    ids=list(dict.fromkeys(ids))
    yield {'type': 'phase', 'phase': 'taste', 'message': f'Resolved {len(ids)} named interests; {len(unresolved)} unresolved'}
    if not ids:
        raise IntegrationError('No unambiguous cultural entities resolved. Add a precise artist, movie, book or brand name.')
    candidates = await client.discover(ids, intent.destination)
    candidates = list({c.id:c for c in candidates}.values())
    yield {'type': 'phase', 'phase': 'discovery', 'message': f'Retrieved {len(candidates)} candidates ({mode})'}
    initially_eligible=[c for c in candidates if not validate(c,intent)]
    affordable,_=select(initially_eligible,intent)
    can_repair=len(initially_eligible)<intent.max_stops or (any(c.cost is not None for c in initially_eligible) and len(affordable)<intent.max_stops)
    if can_repair:
        event={'type':'decision','action':'expand_discovery','message':'Too few eligible or affordable stops; inspect one additional page without relaxing hard requirements.','source':mode}
        decisions.append(event);yield event
        additional=await client.discover(ids,intent.destination,page=2)
        existing={c.id for c in candidates}
        # Separate-page ranks are not numerically comparable. Append the second page
        # in documented affinity order, then recompute ONE pooled ordinal scale.
        candidates.extend(c for c in additional if c.id not in existing)
        candidates=list({c.id:c for c in candidates}.values())
        for index,c in enumerate(candidates):
            c.taste_rank=index+1;c.taste_score=1-index/max(1,len(candidates)-1)
        event={'type':'decision','action':'expansion_complete','message':f'Inspected {len(candidates)} distinct candidates total. Hard requirements unchanged.','source':mode}
        decisions.append(event);yield event
    eligible, rejected = [], []
    for c in candidates:
        reasons = validate(c, intent)
        if reasons:
            rejected.append({'id': c.id, 'name': c.name, 'reasons': reasons})
        else:
            eligible.append(c)
    yield {'type': 'phase', 'phase': 'validation', 'message': f'{len(eligible)} eligible for consideration; {len(rejected)} excluded'}
    if intent.companions and eligible:
        eligible=eligible[:20]
        event={'type':'decision','action':'bounded_pool','message':f'Group negotiation uses the first {len(eligible)} eligible pooled candidates (maximum 20).','source':mode}
        decisions.append(event);yield event
        async for event in attach_member_evidence(eligible,members,resolutions,client,intent,mode):
            decisions.append(event);yield event
    for c in eligible:
        c.score, c.preference_score, matched = score(c, intent)
        signal = 'Synthetic fixture order' if mode == 'fixture' else 'Qloo response order'
        c.explanation = f'{signal}: #{c.taste_rank}. Explicit tag matches: {", ".join(matched) or "none"}. Cultural affinity is not a guarantee of enjoyment.'
        c.warnings = ['Fictional example venue; all costs and signals are synthetic'] if mode == 'fixture' else ['Price, hours, availability, dietary suitability and accessibility are unverified']
    group=None
    if intent.companions:
        selected, fair=optimize(eligible,intent)
        total=fair['known_cost']
        provisional=len(selected)<intent.max_stops and any(c.cost is None for c in eligible)
        discoveries,shown=optimize(eligible,intent,provisional=provisional)
        average,mean_report=optimize(eligible,intent,objective='mean',provisional=provisional)
        without,ablation=optimize(eligible,intent,provisional=provisional,ablate=True)
        group={'strategy':'Maximize minimum best-stop ordinal coverage; then mean coverage, diversity and number of stops; then lower known cost.',
               'scope':'provisional discoveries' if provisional else 'costed fixture itinerary' if mode=='fixture' else 'costed itinerary',
               'is_provisional':provisional,'selected_ids':[c.id for c in discoveries],
               'fair':shown,'mean_objective':mean_report,'without_taste':ablation,
               'minimum_coverage_delta':round(shown['minimum_coverage']-mean_report['minimum_coverage'],6),
               'mean_coverage_tradeoff':round(shown['mean_coverage']-mean_report['mean_coverage'],6),
               'modeled_profiles':len(members),'party_size':intent.party_size,
               'disclaimer':'Ordinal coverage proxies are not human satisfaction. Missing per-person evidence is unknown, conservatively zero. Unknown prices are not budget compliant.',
               'profiles':[{'label':p['label'],'resolved_ids':resolutions[p['label']],
                            'seeds':[s.model_dump() for s in p['seeds']]} for p in members]}
        for c in eligible:
            if c.member_evidence:
                c.score=min(e.proxy for e in c.member_evidence)
                c.explanation+=' Group row score is the lowest member proxy; the final subset balances each member’s best represented stop.'
    else:
        selected, total = select(eligible, intent)
    baseline, _ = select(eligible, intent, True)
    ranked = sorted(eligible, key=lambda c: (-c.score, c.id))
    if intent.companions:
        baseline=without
        ablated_ranked=sorted(eligible,key=lambda c:(-min((e.explicit_alignment for e in c.member_evidence),default=0),c.id))
    else:
        ablated_ranked = sorted(eligible, key=lambda c: (-score(c, intent, True)[0], c.id))
    yield {'type': 'phase', 'phase': 'ranking', 'message': 'Applied taste, preference, diversity and cumulative budget rules'}
    # Runtime guard remains active under python -O. Never relax constraints to fill a plan.
    if (total>intent.effective_budget or len({c.id for c in selected})!=len(selected)
        or any(validate(c,intent) or c.cost is None for c in selected)
        or any(c.source != ('fixture' if mode=='fixture' else 'qloo') for c in candidates)):
        raise IntegrationError('Plan review rejected inconsistent constraints or evidence; no itinerary returned.')
    yield {'type': 'phase', 'phase': 'review', 'message': 'Checked budget, duplicates, evidence labels and hard requirements'}
    chosen = {c.id for c in selected}
    yield {'type': 'result', 'mode': mode, 'intent': intent.model_dump(mode='json'),
           'status': 'simulation' if mode == 'fixture' else 'provisional',
           'itinerary': [c.model_dump(mode='json') for c in selected],
           'alternatives': [c.model_dump(mode='json') for c in ranked if c.id not in chosen],
           'rejected': rejected, 'unresolved': unresolved, 'resolved_ids': ids,
           'group':group,'decisions':decisions,
           'provenance':{'source':'fixture' if mode=='fixture' else 'qloo','retrieved_at':datetime.now(timezone.utc).isoformat(),
                         'resolution_endpoint':'/search','discovery_endpoint':'/v2/insights',
                         'signal_entity_ids':ids,'destination_filter':intent.destination,
                         'practical_verification':'not performed','raw_affinity_used_for_ranking':False},
           'budget': {'known_per_person': total, 'known_group_total': round(total*intent.party_size,2),
                      'limit_per_person': intent.effective_budget, 'complete': bool(selected) and mode == 'fixture'},
           'comparison': {'label': 'Same-candidate per-stop group-floor ablation; subset choices are shown in group tradeoffs. Not an LLM-only comparison' if intent.companions else 'Same-candidate ranking ablation; not an LLM-only comparison',
                          'with_taste': [c.name for c in ranked], 'without_taste': [c.name for c in ablated_ranked],
                          'selected_without_taste': [c.name for c in baseline],
                          'changed_positions': sum(a.id != b.id for a,b in zip(ranked, ablated_ranked))},
           'metrics': {'latency_ms': round((time.perf_counter()-start)*1000,2), 'qloo_calls': client.calls,
                       'candidate_count': len(candidates), 'selected_count': len(selected)},
           'notice': 'Fictional Chicago simulation. No live Qloo calls.' if mode == 'fixture' else
                     'Qloo discoveries are provisional. No confirmed itinerary: prices and visit details require verification.'}
