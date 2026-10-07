"""Sharp fixed-roster bounds from declared selected grades on [0,1]."""
import itertools
import json
import math
from pathlib import Path
from mask_reference_audit import structure
ROOT = Path(__file__).resolve().parent
TOL = 1e-12


def bounds(known, total, scale=(0, 1)):
    if len(scale)!=2 or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in scale):
        raise ValueError('Declare two finite nonboolean score endpoints')
    low, high = scale
    if type(total) is not int or total <= 0 or total < len(known) or not all(math.isfinite(x) for x in scale) or not low < high:
        raise ValueError('Invalid roster or score range')
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or not low <= x <= high for x in known):
        raise ValueError('Grade outside declared finite range')
    missing = total - len(known)
    # Divide before summing: the mean can be finite even when a raw total overflows.
    normalized_sum=math.fsum(x/total for x in known)
    endpoints=(math.fsum([normalized_sum,(missing/total)*low]),
               math.fsum([normalized_sum,(missing/total)*high]))
    if not all(math.isfinite(x) for x in endpoints):
        raise ValueError('Nonfinite computed bounds')
    return endpoints


def compare(a, b):
    for interval in (a,b):
        if len(interval)!=2 or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in interval) or interval[0]>interval[1]:
            raise ValueError('Invalid finite ordered interval')
    gap = (a[0]-b[1], a[1]-b[0])
    if not all(math.isfinite(x) for x in gap):
        raise ValueError('Gap overflow')
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
        models,tasks,grades,masks,categories = structure(working,field,value,allow_unknown_models=(rule == 'exporter'))
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

def report_selected(rows, tasks, models, scale=(0,1)):
    """Bound a declared common roster using only selected/available grades."""
    if not tasks or len(tasks) != len(set(tasks)) or len(models)<2 or len(models)!=len(set(models)):
        raise ValueError('Declare unique task IDs and at least two unique models')
    allowed=set(tasks); known={m:[] for m in models}; seen=set()
    for row in rows:
        key=(row['model'],row['task_id'])
        if key in seen: raise ValueError('Duplicate model/task identity')
        seen.add(key)
        if key[0] not in known or key[1] not in allowed:
            raise ValueError('Record outside declared model/task roster')
        if row.get('score_scale') != list(scale):
            raise ValueError('Incompatible declared score scale')
        available=row.get('score_available')
        if type(available) is not bool:
            raise ValueError('Declare score_available as boolean')
        score=row.get('native_score')
        if available:
            if isinstance(score,bool) or not isinstance(score,(int,float)):
                raise ValueError('Available score must be numeric')
            known[key[0]].append(score)
        elif score is not None:
            raise ValueError('Unavailable score must be null or absent')
    intervals={}
    for m in models:
        lo,hi=bounds(known[m],len(tasks),scale)
        intervals[m]={'lower':lo,'upper':hi,'known':len(known[m]),'roster':len(tasks)}
    pairs=[]
    for a,b in itertools.combinations(models,2):
        gap,order=compare((intervals[a]['lower'],intervals[a]['upper']),(intervals[b]['lower'],intervals[b]['upper']))
        pairs.append({'models':[a,b],'gap_bounds':gap,'certified_order':([a,b] if order>0 else [b,a]) if order else None})
    return {'models':intervals,'pairs':pairs,'interpretation':'Bounds on the explicitly declared roster/range; unresolved is not a tie or inferred failure.'}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ledger',nargs='?')
    parser.add_argument('--roster',help='JSON object with tasks and models lists')
    parser.add_argument('--score-range',nargs=2,type=float,default=[0,1])
    args=parser.parse_args()
    if args.ledger:
        if not args.roster: parser.error('--roster is required for selected-ledger reporting')
        roster=json.loads(Path(args.roster).read_text())
        rows=[json.loads(x) for x in Path(args.ledger).read_text().splitlines()]
        print(json.dumps(report_selected(rows,roster['tasks'],roster['models'],args.score_range),indent=2,allow_nan=False))
    else:
        if args.roster: parser.error('Provide a ledger with --roster')
        rows=[json.loads(x) for x in (ROOT/'run_accounting/wildclaw_released_pairs.jsonl').read_text().splitlines()]
        report=audit(rows)
        (ROOT/'bounded_comparison_results.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        print({k:{x:v[x] for x in ['pairs','certified_pairs','unresolved_pairs','incorrect_certificates_against_held_out_recorded_grades','naive_filtered_reversals']} for k,v in report['rules'].items()})
