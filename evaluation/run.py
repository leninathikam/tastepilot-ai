"""Reproducible fixture-only ablation; not evidence of real Qloo performance."""
import asyncio
import json
from pathlib import Path
from backend.app.fixtures import FixtureClient
from backend.app.models import Intent, Seed
from backend.app.planner import plan

ROOT=Path(__file__).resolve().parent


async def main():
    scenarios=[]
    for i in range(15):
        scenarios.append({'id':f'fixture-{i+1:02}', 'intent':Intent(
            date='2026-10-31',budget=[0,20,50,100,150][i%5],party_size=1+i%4,
            seeds=[Seed(name=['Japanese Breakfast','Radiohead','Khruangbin'][i%3])],
            interests=[['Korean food'],['indie music'],['contemporary art'],['Korean food','indie music'],['Korean food','indie music','contemporary art']][i%5],
            accessible=i%3==1, dietary='vegetarian' if i%3==2 else 'none',
        ).model_dump(mode='json')})
    results=[]
    for scenario in scenarios:
        intent=Intent.model_validate(scenario['intent'])
        events=[e async for e in plan(intent,FixtureClient(),'fixture')]
        repeated=[e async for e in plan(intent,FixtureClient(),'fixture')]
        r=events[-1]
        selected=r['itinerary']
        tags=' '.join(tag.casefold() for c in selected for tag in c['tags'])
        results.append({'scenario':scenario['id'],'output':r,'metrics':{
            'budget_satisfied':r['budget']['known_per_person']<=intent.budget,
            'hard_constraints_satisfied':all((not intent.accessible or c['accessible'] is True) and (intent.dietary=='none' or intent.dietary in c['dietary']) for c in selected),
            'interest_coverage':sum(s.casefold() in tags for s in intent.interests)/max(1,len(intent.interests)),
            'category_count':len({c['category'] for c in selected}),
            'repeat_order_stable':[c['id'] for c in selected]==[c['id'] for c in repeated[-1]['itinerary']],
            'fixture_label_coverage':sum(c['source']=='fixture' for c in selected)/len(selected) if selected else None,
            'unsupported_factual_claim_rate':None,
            'estimated_operating_cost':None,
        }})
    aggregate={'scope':'15 synthetic fixture scenarios; no live API or LLM baseline',
               'scenarios':len(results),'budget_pass':sum(r['metrics']['budget_satisfied'] for r in results),
               'hard_constraints_pass':sum(r['metrics']['hard_constraints_satisfied'] for r in results),
               'stable_order':sum(r['metrics']['repeat_order_stable'] for r in results),
               'mean_interest_coverage':round(sum(r['metrics']['interest_coverage'] for r in results)/len(results),3),
               'scenarios_with_changed_ranking':sum(r['output']['comparison']['changed_positions']>0 for r in results),
               'qloo_calls':0,'llm_baseline':'NOT RUN','unsupported_claim_audit':'NOT RUN; labels checked only'}
    for directory in ('datasets','results'):(ROOT/directory).mkdir(exist_ok=True)
    (ROOT/'datasets/scenarios.json').write_text(json.dumps(scenarios,indent=2),encoding='utf-8')
    (ROOT/'results/raw.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    (ROOT/'results/aggregate.json').write_text(json.dumps(aggregate,indent=2),encoding='utf-8')
    print(json.dumps(aggregate,indent=2))


if __name__=='__main__':asyncio.run(main())
