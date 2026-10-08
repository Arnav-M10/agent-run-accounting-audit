"""Retrospective recorded-mean selection and bounded winner reporting.

This is an application of interval bounds, not a novel selection algorithm.
The demonstration deliberately hides grades already supplied in the release.
"""
import json
import math
from pathlib import Path
from bounded_comparison import TOL, compare, report_selected
from mask_reference_audit import structure
ROOT=Path(__file__).resolve().parent


def report_winners(rows, tasks, models, scale=(0,1)):
    """Declare possible co-maximizers within tolerance and strict certificates."""
    report=report_selected(rows,tasks,models,scale)
    intervals={m:(v['lower'],v['upper']) for m,v in report['models'].items()}
    candidates=[]; certified=[]; ruled_out={}
    for m in models:
        dominators=[other for other in models if other!=m and compare(intervals[other],intervals[m])[1]==1]
        if dominators:ruled_out[m]=dominators
        else:candidates.append(m)
        if all(compare(intervals[m],intervals[other])[1]==1 for other in models if other!=m):
            certified.append(m)
    return {'models':report['models'],
            'not_ruled_out_as_roster_maximizer':candidates,
            'certified_strict_roster_maximizer':certified,
            'ruled_out_by':ruled_out,
            'tolerance':TOL,
            'interpretation':'Maximizers of the declared equally weighted recorded-grade roster within numerical tolerance. Independently unrestricted unavailable grades permit each candidate to attain its upper endpoint while other models attain their lower endpoints. Candidates are separate possibilities, not simultaneously achievable strict winners. No statistical, deployment, outcome-validation or general agent-quality claim.'}


def maximizers(means):
    best=max(means.values())
    return [m for m in means if best-means[m]<=TOL]


def demonstrate(rows):
    result={'target':'Choose a maximizer of the equally weighted recorded-grade mean on the released common task roster. This is a retrospective fixed-release decision illustration, not a demonstrated consumer decision or deployment selection policy.',
            'missingness':'All grades exist in WildClawBench. Bounds below deliberately hide ineligible grades to illustrate eligible-only reuse; use all available grades instead when available.', 'rules':{}}
    for rule,field,value in [('assistant','last_original_role','assistant'),('native_stop','native_stop_reason','stop'),('exporter','execution_status','completed')]:
        working=[dict(r) for r in rows]
        if rule=='native_stop':
            for r in working:
                if r.get(field) is None:
                    if r.get('last_original_role')=='assistant':raise ValueError('Unknown assistant stop reason')
                    r[field]='__no_assistant_stop_event__'
        models,tasks,grades,masks,_=structure(working,field,value,allow_unknown_models=rule=='exporter')
        full={m:math.fsum(g)/len(tasks) for m,g in zip(models,grades)}
        conditional={}
        for m,g,mask in zip(models,grades,masks):
            known=[x for x,yes in zip(g,mask) if yes]
            if not known:raise ValueError('Empty conditional population')
            conditional[m]=math.fsum(known)/len(known)
        selected=[{'model':m,'task_id':t,'score_available':True,'native_score':grade,'score_scale':[0,1]} for m,g,mask in zip(models,grades,masks) for t,grade,yes in zip(tasks,g,mask) if yes]
        bounded=report_winners(selected,tasks,models)
        naive=maximizers(conditional); target=maximizers(full)
        result['rules'][rule]={'models':models,'tasks':len(tasks),
            'full_roster_means':full,'conditional_means':conditional,
            'conditional_mean_maximizers':naive,'full_roster_maximizers':target,
            'retrospective_recorded_mean_loss_percentage_points':{m:100*(max(full.values())-full[m]) for m in naive},
            'masked_grade_winner_report':bounded}
    return result


if __name__=='__main__':
    rows=[json.loads(x) for x in (ROOT/'run_accounting/wildclaw_released_pairs.jsonl').read_text().splitlines()]
    result=demonstrate(rows)
    (ROOT/'winner_decision_results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    for rule,r in result['rules'].items():
        print(rule,{'conditional_choice':r['conditional_mean_maximizers'],'roster_choice':r['full_roster_maximizers'],'observed_target_loss_pp':r['retrospective_recorded_mean_loss_percentage_points'],'bounded_candidates':len(r['masked_grade_winner_report']['not_ruled_out_as_roster_maximizer']),'certified_winner':r['masked_grade_winner_report']['certified_strict_roster_maximizer']})
