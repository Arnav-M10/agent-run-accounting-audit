"""Sharp fixed-roster bounds from declared selected grades on [0,1]."""
import itertools
import json
import math
from pathlib import Path
from mask_reference_audit import structure
ROOT = Path(__file__).resolve().parent
TOL = 1e-12


def bounds(known, total, scale=(0, 1)):
    low, high = scale
    if total <= 0 or total < len(known) or not low < high:
        raise ValueError('Invalid roster or score range')
    if any(not math.isfinite(x) or not low <= x <= high for x in known):
        raise ValueError('Grade outside declared finite range')
    missing = total - len(known)
    return ((math.fsum(known) + missing * low)/total,
            (math.fsum(known) + missing * high)/total)


def compare(a, b):
    gap = (a[0]-b[1], a[1]-b[0])
    order = 1 if gap[0] > TOL else -1 if gap[1] < -TOL else 0
    return gap, order


def audit(rows):
    report = {'interpretation': 'Masked-grade demonstration: omitted grades are deliberately hidden despite being present in this release. Bounds describe recorded grades, not independently validated outcomes.', 'rules': {}}
    for rule,field,value in [('assistant','last_original_role','assistant'),('native_stop','native_stop_reason','stop'),('exporter','execution_status','completed')]:
        working = [dict(r) for r in rows]
        if field == 'native_stop_reason':
            for row in working:
                if row.get(field) is None:
                    if row.get('last_original_role') == 'assistant':
                        raise ValueError('Unknown stop reason on assistant ending')
                    row[field]='__no_assistant_stop_event__'
        models,tasks,grades,masks,categories = structure(working,field,value)
        intervals = {}
        conditional = {}
        truth = {}
        for m,g,mask in zip(models,grades,masks):
            known = [x for x,yes in zip(g,mask) if yes]
            lower,upper=bounds(known,len(tasks))
            intervals[m]={'lower':lower,'upper':upper,'known':len(known),'roster':len(tasks)}
            conditional[m]=math.fsum(known)/len(known)
            truth[m]=math.fsum(g)/len(g)
        certificates=[]; unresolved=[]; naive_reversals=incorrect=0
        for a,b in itertools.combinations(models,2):
            gap,order=compare((intervals[a]['lower'],intervals[a]['upper']),(intervals[b]['lower'],intervals[b]['upper']))
            native_gap=truth[a]-truth[b]
            naive_reversals += (conditional[a]-conditional[b])*native_gap < 0
            row={'models':[a,b],'gap_bounds':gap}
            if order:
                row['certified_order']= [a,b] if order>0 else [b,a]
                certificates.append(row)
                incorrect += order*native_gap <= TOL
            else: unresolved.append(row)
        report['rules'][rule]={'models':intervals,'pairs':len(certificates)+len(unresolved),'certified_pairs':len(certificates),'unresolved_pairs':len(unresolved),'incorrect_certificates_against_held_out_recorded_grades':incorrect,'naive_filtered_reversals':naive_reversals,'certificates':certificates,'unresolved':unresolved}
    return report

if __name__=='__main__':
    rows=[json.loads(x) for x in (ROOT/'run_accounting/wildclaw_released_pairs.jsonl').read_text().splitlines()]
    report=audit(rows)
    (ROOT/'bounded_comparison_results.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print({k:{x:v[x] for x in ['pairs','certified_pairs','unresolved_pairs','incorrect_certificates_against_held_out_recorded_grades','naive_filtered_reversals']} for k,v in report['rules'].items()})
