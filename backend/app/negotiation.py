"""Bounded, deterministic group compromise. Scores are ordinal proxies, not satisfaction."""
from itertools import combinations
from .models import MemberEvidence


FOOD_MODIFIERS = (' food', ' cuisine', ' meals', ' cooking', ' restaurant')


def profiles(intent):
    return [{'label':'You','seeds':intent.seeds,'interests':intent.interests}]+[
        {'label':p.label,'seeds':p.seeds,'interests':p.interests} for p in intent.companions]


def matches_tag(interest: str, normalized_tags: set[str]) -> bool:
    if interest in normalized_tags:
        return True
    for mod in FOOD_MODIFIERS:
        if interest.endswith(mod):
            stem = interest[:-len(mod)].strip()
            if stem in normalized_tags:
                return True
    return False


def alignment(tags, interests):
    normalized = {s.casefold().strip() for s in tags}
    unique = list(dict.fromkeys(s.casefold().strip() for s in interests))
    matched = [s for s in unique if matches_tag(s, normalized)]
    return len(matched) / max(1, len(unique)), matched


async def attach_member_evidence(candidates, member_profiles, resolutions, client, intent, mode):
    ids=[c.id for c in candidates]
    for member in member_profiles:
        resolved=resolutions[member['label']]
        returned=await client.discover(resolved,intent.destination,entity_ids=ids)
        by_id={c.id:c for c in returned if c.id in ids}
        for c in candidates:
            row=by_id.get(c.id)
            explicit,matched=alignment(c.tags,member['interests'])
            ordinal=row.taste_score if row is not None else None
            proxy=(intent.taste_weight*(ordinal if ordinal is not None else 0)+intent.preference_weight*explicit)/(intent.taste_weight+intent.preference_weight)
            c.member_evidence.append(MemberEvidence(label=member['label'],source='fixture' if mode=='fixture' else 'qloo',resolved_ids=resolved,
                returned_rank=row.taste_rank if row else None,ordinal_signal=ordinal,
                explicit_alignment=explicit,matched_interests=matched,proxy=proxy,raw_query=row.raw_query if row else {},
                note='Within-query ordinal proxy, not predicted satisfaction.' if row else 'Not returned for this profile; unknown evidence contributes zero conservatively, not dislike.'))
        yield {'type':'decision','action':'member_evidence','message':f"Compared the same {len(ids)} candidates for {member['label']}; {len(by_id)} returned", 'source':mode}


def coverage(selected, labels, ablate=False):
    return {label:max((e.explicit_alignment if ablate else e.proxy
                      for c in selected for e in c.member_evidence if e.label==label),default=0)
            for label in labels}


def optimize(candidates, intent, objective='fair', provisional=False, ablate=False):
    # Exhaustive search only within 20 candidates, <=6 stops: <=60,459 subsets.
    pool=sorted(candidates,key=lambda c:c.id)[:20]
    if not provisional:
        pool=[c for c in pool if c.cost is not None]
    labels=[p['label'] for p in profiles(intent)]
    best,best_key,best_coverage=[],None,dict.fromkeys(labels,0)
    examined=0
    for size in range(1,min(intent.max_stops,len(pool))+1):
        for subset in combinations(pool,size):
            examined+=1
            known_cost=sum(c.cost or 0 for c in subset)
            if known_cost>intent.effective_budget:
                continue
            values=coverage(subset,labels,ablate)
            floor=min(values.values());mean=sum(values.values())/len(labels)
            primary=(floor,mean) if objective=='fair' else (mean,floor)
            key=(*primary,len({c.category for c in subset}),len(subset),-known_cost)
            if best_key is None or key>best_key:
                best,best_key,best_coverage=list(subset),key,values
    return best, {'member_coverage':best_coverage,'minimum_coverage':min(best_coverage.values()),
                  'mean_coverage':sum(best_coverage.values())/len(labels),'subsets_examined':examined,
                  'known_cost':round(sum(c.cost or 0 for c in best),2),
                  'unknown_cost_count':sum(c.cost is None for c in best),
                  'ids':[c.id for c in best]}
