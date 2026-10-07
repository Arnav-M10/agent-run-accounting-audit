"""Exact descriptive thinning reference for retained-pass oracle opportunity."""
import collections
import json
from fractions import Fraction
from math import comb
from pathlib import Path
ROOT=Path(__file__).resolve().parent


def thinning_probability(successes, selected):
    if type(successes) is not int or type(selected) is not int or not 0<=successes<=4 or not 0<=selected<=4:
        raise ValueError('Declare integer success/pass counts in 0..4')
    return Fraction(1) - Fraction(comb(4-successes,selected),comb(4,selected))


def audit(attempts, slots):
    by_id={}
    for row in attempts:
        if row['attempt_id'] in by_id:raise ValueError('Duplicate attempt identity')
        by_id[row['attempt_id']]=row
    groups=collections.defaultdict(dict)
    for slot in slots:
        key=(slot['model'],slot['domain'],slot['task_id'])
        if type(slot['pass']) is not int or not 1<=slot['pass']<=4:raise ValueError('Invalid pass slot')
        if slot['pass'] in groups[key]:raise ValueError('Duplicate slot')
        if slot['observed_attempt_id'] is None:record=None
        else:
            record=by_id[slot['observed_attempt_id']]
            if any(record[f]!=slot[f] for f in ['model','domain','task_id','pass']):raise ValueError('Slot/record mismatch')
            if record['score_scale'] != [0,1] or type(record['native_score']) not in (int,float) or record['native_score'] not in (0,1) or record['score_available'] is not True:raise ValueError('Requires binary search grades')
        groups[key][slot['pass']]=record
    donors=collections.defaultdict(list); incomplete=collections.defaultdict(list)
    for (model,domain,task),passes in groups.items():
        if set(passes)!=set(range(1,5)):raise ValueError('Requires reconstructed four-slot grid')
        retained=[r for r in passes.values() if r is not None and r['retention']=='retained']
        s=sum(int(r['native_score']) for r in retained);k=len(retained)
        if k==4:donors[(model,domain)].append(tuple(int(passes[i]['native_score']) for i in range(1,5)))
        else:incomplete[(model,domain,k)].append({'oracle':int(s>0),'pass_mask':tuple(i-1 for i in range(1,5) if passes[i] is not None and passes[i]['retention']=='retained')})
    cells=[]; count=actual=0; thinned=Fraction(0); actual_mask=Fraction(0); full=Fraction(0); unsupported=[]
    for (model,domain,k),outcomes in sorted(incomplete.items()):
        donor=donors[(model,domain)];n=len(outcomes)
        probability=sum((thinning_probability(sum(s),k) for s in donor),Fraction(0))/len(donor) if donor else (Fraction(0) if k==0 else None)
        full_probability=Fraction(sum(sum(s)>0 for s in donor),len(donor)) if donor else None
        mask_probability=Fraction(sum(any(d[i] for i in o['pass_mask']) for d in donor for o in outcomes),len(donor)*n) if donor else (Fraction(0) if k==0 else None)
        row={'model':model,'domain':domain,'retained_pass_count':k,'incomplete_groups':n,'observed_oracle_successes':sum(o['oracle'] for o in outcomes),'complete_donor_groups':len(donor),'thinned_reference_probability':float(probability) if probability is not None else None,'full_donor_probability':float(full_probability) if full_probability is not None else None,'actual_pass_mask_reference_probability':float(mask_probability) if mask_probability is not None else None}
        cells.append(row)
        if probability is None or full_probability is None:
            unsupported.append(row);continue
        count+=n;actual+=sum(o['oracle'] for o in outcomes);thinned+=n*probability;full+=n*full_probability;actual_mask+=n*mask_probability
    return {'interpretation':'Outcome-informed donor/thinning reference with changed population weights, not a causal decomposition or recovery of omitted outcomes.','cells':cells,'supported_summary':{'groups':count,'observed_successes':actual,'observed_probability':actual/count if count else None,'thinned_expected_successes':float(thinned),'thinned_probability':float(thinned/count) if count else None,'actual_pass_mask_expected_successes':float(actual_mask),'actual_pass_mask_probability':float(actual_mask/count) if count else None,'full_donor_expected_successes':float(full),'full_donor_probability':float(full/count) if count else None,'reference_opportunity_reduction_points':float(100*(full-thinned)/count) if count else None,'remaining_observed_reference_gap_points':float(100*(thinned-actual)/count) if count else None},'unsupported_cells':unsupported,'incomplete_groups_total':sum(map(len,incomplete.values()))}

if __name__=='__main__':
    attempts=[json.loads(x) for x in (ROOT/'run_accounting/cmu_attempts.jsonl').read_text().splitlines()]
    slots=[json.loads(x) for x in (ROOT/'run_accounting/cmu_search_slots.jsonl').read_text().splitlines()]
    result=audit(attempts,slots)
    (ROOT/'oracle_opportunity_results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['supported_summary'],indent=2));print('Unsupported:',result['unsupported_cells'])
