"""Synthetic algorithm evaluation. This is NOT evidence of real Qloo quality."""
import asyncio
import json
from pathlib import Path
from backend.app.models import Intent, Candidate
from backend.app.fixtures import FixtureClient
from backend.app.planner import plan, validate
from backend.app.qloo import IntegrationError

ROOT=Path(__file__).resolve().parent


def scenarios():
    base={'date':'2026-10-31','destination':'Chicago','party_size':3,'budget':150,
          'seeds':[{'name':'Japanese Breakfast','category':'artist'}], 'interests':['Korean food'],
          'companions':[{'label':'Music friend','seeds':[{'name':'Radiohead','category':'artist'}]},
                        {'label':'Film friend','seeds':[{'name':'Past Lives','category':'movie'}]}]}
    variants=[('one-stop',{'max_stops':1}),('two-stops',{'max_stops':2}),('three-stops',{}),
              ('zero-budget',{'budget':0}),('small-budget',{'budget':8}),('budget-20',{'budget':20}),
              ('budget-40',{'budget':40}),('access',{'accessible':True}),('vegetarian',{'dietary':'vegetarian'}),
              ('vegan',{'dietary':'vegan'}),('unknown-hours',{'require_verified_hours':True}),
              ('replacement',{'excluded_ids':['fixture:0','fixture:1']}),('outside-fixture-city',{'destination':'Paris'}),
              ('guest-cap',{'companions':[{'label':'Guest','seeds':[{'name':'Dune','category':'book'}],'budget':12}]}),
              ('unresolved-member',{'companions':[{'label':'Guest','seeds':[{'name':'Imaginary artist','category':'artist'}]}]})]
    return [{'id':name,'intent':{**base,**change},'expected_error':name=='unresolved-member'} for name,change in variants]


async def evaluate():
    records=[]
    for scenario in scenarios():
        intent=Intent.model_validate(scenario['intent'])
        try:
            events=[e async for e in plan(intent,FixtureClient(),'fixture')]
            output=events[-1]
            repeated=[e async for e in plan(intent,FixtureClient(),'fixture')]
            selected=output['itinerary']
            group=output['group']
            records.append({'scenario':scenario['id'],'output':output,'checks':{
                'expected_outcome':not scenario['expected_error'],
                'nonempty_itinerary':bool(selected),'selected_stops':len(selected),
                'budget_satisfied':output['budget']['known_per_person']<=intent.effective_budget,
                'hard_constraints_satisfied':all(not validate(Candidate.model_validate(c),intent) for c in selected),
                'minimum_coverage_not_worse_than_mean':group['minimum_coverage_delta']>=-1e-9,
                'strict_fairness_improvement':group['minimum_coverage_delta']>1e-9,
                'mean_tradeoff':group['mean_coverage_tradeoff'],
                'taste_ablation_changes_selection':set(group['selected_ids'])!=set(group['without_taste']['ids']),
                'stable_selection':group['selected_ids']==repeated[-1]['group']['selected_ids'],
                'all_evidence_is_fixture':all(e['source']=='fixture' for c in selected for e in c['member_evidence']),
            }})
        except IntegrationError as exc:
            records.append({'scenario':scenario['id'],'error':str(exc),'checks':{'expected_outcome':scenario['expected_error']}})
    success=[r for r in records if 'output' in r]
    aggregate={'scope':'Synthetic group algorithm checks; no live Qloo or LLM calls',
        'scenario_count':len(records),'expected_outcomes':sum(r['checks']['expected_outcome'] for r in records),
        'completed_plans':len(success),'nonempty_itineraries':sum(r['checks']['nonempty_itinerary'] for r in success),
        'empty_itineraries':sum(not r['checks']['nonempty_itinerary'] for r in success),
        'budget_pass':sum(r['checks']['budget_satisfied'] for r in success),
        'hard_constraints_pass':sum(r['checks']['hard_constraints_satisfied'] for r in success),
        'minimum_coverage_not_worse_than_mean':sum(r['checks']['minimum_coverage_not_worse_than_mean'] for r in success),
        'strict_fairness_improvement':sum(r['checks']['strict_fairness_improvement'] for r in success),
        'taste_ablation_changes_selection':sum(r['checks']['taste_ablation_changes_selection'] for r in success),
        'stable_selection':sum(r['checks']['stable_selection'] for r in success),
        'live_qloo_verified':False,'llm_baseline':'NOT RUN','human_satisfaction':'NOT MEASURED',
        'warning':'Safety passes on empty plans are not planning success. Fairness is an optimized proxy, not measured satisfaction.'}
    (ROOT/'datasets/group_scenarios.json').write_text(json.dumps(scenarios(),indent=2),encoding='utf-8')
    (ROOT/'results/group_raw.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    (ROOT/'results/group_aggregate.json').write_text(json.dumps(aggregate,indent=2),encoding='utf-8')
    print(json.dumps(aggregate,indent=2))

if __name__=='__main__':asyncio.run(evaluate())
