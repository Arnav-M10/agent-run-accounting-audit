#!/usr/bin/env python3
"""Replay the released aggregate audit using only the Python standard library."""
import argparse, collections, hashlib, itertools, json, math
from pathlib import Path
TOL=1e-8

def close(a,b): return math.isclose(a,b,rel_tol=0,abs_tol=TOL)

def validate(rows):
    if len(rows)!=150: raise ValueError('Expected all 150 released rows')
    keys=[(r['agent'],r['model'],r['benchmark']) for r in rows]
    if len(set(keys))!=150: raise ValueError('Duplicate aggregate key')
    agents=set(k[0] for k in keys); models=set(k[1] for k in keys); benchmarks=set(k[2] for k in keys)
    if (len(agents),len(models),len(benchmarks))!=(5,5,6):raise ValueError('Expected 5 agents x 5 models x 6 benchmarks')
    if set(keys)!=set(itertools.product(agents,models,benchmarks)):raise ValueError('Incomplete released grid')
    countfields=['planned_sessions','total_sessions','completed_sessions','incomplete_sessions','missing_sessions','successful_sessions']
    for r in rows:
        for field in ['average_score','benchmark_score']+countfields:
            value=r[field]
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError('Non-finite/non-numeric '+field)
        for field in countfields:
            if r[field]<0 or not close(r[field],round(r[field])):raise ValueError('Invalid count '+field)
        for field in ['average_score','benchmark_score']:
            if not 0<=r[field]<=1:raise ValueError('Score outside [0,1]')

def audit(payload):
    rows=payload['rows']; validate(rows); out=[]
    for i,r in enumerate(rows):
        b=r['benchmark']; n=r['planned_sessions']; t=r['total_sessions']; c=r['completed_sessions']
        a=r['average_score']; s=r['benchmark_score']
        identity={'swebench':'binary_issue_resolution','browsecompplus':'binary_answer_correctness','appworld_test_normal':'different_metrics_partial_test_completion_vs_task_goal_completion'}.get(b,'reward_metric_comparability_not_verified')
        # Products imply resolved totals only for SWE-bench and only under complete numeric-score coverage.
        inferred_a=a*t if b=='swebench' else None
        inferred_b=s*c if b=='swebench' else None
        equal=inferred_a is not None and close(inferred_a,inferred_b)
        eligible=b=='swebench' and t>0 and c>0 and equal and close(inferred_a,round(inferred_a)) and close(inferred_b,round(inferred_b))
        strict=eligible and n==t
        z={'numeric_grade_count_released':None,'eligibility_requires_all_recorded_scores_numeric':True,'row_index':i,'key':[r['agent'],r['model'],b],'metric_identity':identity,'score_difference':s-a,'different_scores':not close(s,a),'planned_recorded_gap':n-t,'running_sessions_released':r.get('running_sessions'),'status_coverage_gap_excluding_unreleased_running':n-(c+r['incomplete_sessions']+r['missing_sessions']+r.get('running_sessions',0)),'positive_incomplete':r['incomplete_sessions']>0,'implied_average_resolved_total':inferred_a,'implied_benchmark_resolved_total':inferred_b,'equal_implied_resolved_totals':equal if b=='swebench' else None,'eligible_recorded_denominator_comparison':eligible,'eligible_planned_equals_recorded_comparison':strict,'conditional_denominator_difference_candidate':eligible and not close(s,a),'implied_resolved_count_if_numeric_coverage_complete':round(inferred_a) if eligible else None}
        out.append(z)
    counts={}
    for b in sorted(set(r['benchmark'] for r in rows)):
        q=[x for x in out if x['key'][2]==b]
        counts[b]={'rows':len(q),'different_scores':sum(x['different_scores'] for x in q),'positive_incomplete':sum(x['positive_incomplete'] for x in q),'planned_recorded_gap_rows':sum(x['planned_recorded_gap']!=0 for x in q),'status_coverage_gap_rows':sum(x['status_coverage_gap_excluding_unreleased_running']!=0 for x in q),'eligible_recorded_rows':sum(x['eligible_recorded_denominator_comparison'] for x in q),'eligible_strict_rows':sum(x['eligible_planned_equals_recorded_comparison'] for x in q),'conditional_denominator_difference_candidate_rows':sum(x['conditional_denominator_difference_candidate'] for x in q)}
    def pairs(flag):
        items=[(r,x) for r,x in zip(rows,out) if x[flag]]; comparisons=[]
        for (a,aa),(b,bb) in itertools.combinations(items,2):
            if a['model']!=b['model']:continue
            da=a['average_score']-b['average_score']; db=a['benchmark_score']-b['benchmark_score']
            sign=lambda d:0 if close(d,0) else (1 if d>0 else -1)
            sa,sb=sign(da),sign(db)
            comparisons.append({'model':a['model'],'row_indices':[aa['row_index'],bb['row_index']],'agents':[a['agent'],b['agent']],'average_score_difference':da,'benchmark_score_difference':db,'strict_order_flip':sa*sb==-1,'tie_change':(sa==0)!=(sb==0)})
        return {'eligible_pairs':len(comparisons),'strict_order_flips':sum(x['strict_order_flip'] for x in comparisons),'tie_changes':sum(x['tie_change'] for x in comparisons),'comparisons':comparisons}
    return {'eligibility_policy':'Conditional aggregate evidence only: assumes every recorded SWE result contributes a numeric score; public release does not expose that count. Equal implied products do not verify actual numerator or individual outcomes.','tolerance_absolute':TOL,'rows':len(rows),'distinct_keys':len(set(tuple(x['key']) for x in out)),'missing_sessions_nonzero_rows':sum(r['missing_sessions']!=0 for r in rows),'benchmark_counts':counts,'row_audit':out,'recorded_denominator_pair_audit':pairs('eligible_recorded_denominator_comparison'),'planned_equals_recorded_pair_audit':pairs('eligible_planned_equals_recorded_comparison')}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',default=str(Path(__file__).with_name('released_aggregates.json')));p.add_argument('--output');args=p.parse_args()
    result=audit(json.loads(Path(args.input).read_text())); text=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if args.output:Path(args.output).write_text(text)
    else:print(text,end='')
