"""Apply the unmodified generic reporter to a second release's recorded grades.

Documentation-only exclusions are not fabricated as ledger rows. This demo
reports released records; it does not reproduce the all-initiated zero policy.
"""
import json
import math
from pathlib import Path
from summarize_ledger import summarize


def demonstrate(root):
    expected=json.loads((root/'audit_results.json').read_text())['benchmark']
    path=root/'run_accounting/cmu_attempts.jsonl'
    output={}
    comparisons=0
    for name,rules in [('retained',[('retention','retained')]),('all_released',[])]:
        report=summarize(path,['benchmark'],rules,'error')
        report['ledger']='run_accounting/cmu_attempts.jsonl'
        for group in report['groups']:
            benchmark=group['group'][0]['value']; reference=expected[benchmark]
            n=(reference['retained'] if name=='retained' else
               reference['original_attempts']-reference['round1_unreleased'])
            total=reference['retained_reward_sum']+(reference['positive_removed_reward_sum'] if name=='all_released' else 0)
            assert group['population_count']==n and group['scored_count']==n
            assert math.isclose(group['policy_score_mean'],total/n,abs_tol=1e-12,rel_tol=0)
            comparisons+=1
        output[name]=report
    try:
        summarize(path,[],[],'error')
    except ValueError as exc:
        assert 'mixed declared score scales' in str(exc)
        output['pooled_native_scales']={'rejected':True,'reason':'Mixed [0,1] and [0,10] scales; no automatic normalization.'}
    else:raise AssertionError('Unsafe mixed-scale pooling accepted')
    output['verification']={'matched_benchmark_population_means':comparisons,
        'recorded_retained_population':8653,'recorded_released_population':9769,
        'documented_but_unreleased_exclusions':329,
        'interpretation':'Recorded-grade summaries on released records; documentation-only exclusions remain outside the row ledger. Not all-initiated exclusion-zero scoring.'}
    return output

if __name__=='__main__':
    root=Path(__file__).resolve().parent
    result=demonstrate(root)
    (root/'cmu_reporting_example.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(result['verification'])
