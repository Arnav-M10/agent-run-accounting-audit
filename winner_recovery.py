"""Recorded winner recovery: exact offline certificate and fixed blinded policy.

No inference calls. Querying retrieves deliberately withheld existing grades.
The offline minimum uses true recorded grades, and is not a prospective budget.
"""
import argparse
import json
import math
import itertools
import random
from pathlib import Path
from mask_reference_audit import structure
from fractions import Fraction
TOL = Fraction("0.000000000001")

def exact(x):
    """Canonical JSON numeric decimal interpreted exactly, never binary rounded."""
    return Fraction(str(x))

def bounds(values, n):
    total = sum((exact(v) for v in values), Fraction(0))
    return total/n, (total+n-len(values))/n


def optimal(grades, masks, winner):
    n=len(grades[0]); M=len(grades)
    intervals=[bounds([x for x,keep in zip(g,mask) if keep],n) for g,mask in zip(grades,masks)]
    ranked=[]; prefix=[]
    for m,(g,mask) in enumerate(zip(grades,masks)):
        gains=sorted([((exact(x) if m==winner else 1-exact(x))/n,t) for t,(x,k) in enumerate(zip(g,mask)) if not k],reverse=True)
        ranked.append(gains); prefix.append([sum((v for v,_ in gains[:k]), Fraction(0)) for k in range(len(gains)+1)])
    options=[]
    for k,gain in enumerate(prefix[winner]):
        lower=intervals[winner][0]+gain
        chosen={winner:k}; feasible=True
        for m in range(M):
            if m==winner: continue
            q=next((j for j,reduction in enumerate(prefix[m]) if lower-(intervals[m][1]-reduction)>TOL),None)
            if q is None: feasible=False;break
            chosen[m]=q
        if feasible: options.append((sum(chosen.values()),k,chosen))
    if not options:return None
    total,k,chosen=min(options,key=lambda a:(a[0],a[1]))
    disclosures=[(m,t) for m,q in chosen.items() for _,t in ranked[m][:q]]
    updated=[list(mask) for mask in masks]
    for m,t in disclosures:updated[m][t]=True
    after=[bounds([x for x,keep in zip(g,mask) if keep],n) for g,mask in zip(grades,updated)]
    assert all(after[winner][0]-after[m][1]>TOL for m in range(M) if m!=winner)
    return {'count':total,'own_winner_count':k,'by_model':chosen,'disclosures':disclosures,'winner_lower_after':float(after[winner][0]),'largest_competitor_upper_after':float(max(after[m][1] for m in range(M) if m!=winner)),'all_available_omitted_count':sum(not k for mask in masks for k in mask)}

def brute(grades,masks,w):
    slots=[(m,t) for m,mask in enumerate(masks) for t,k in enumerate(mask) if not k]
    for c in range(len(slots)+1):
        for restored in itertools.combinations(slots,c):
            updated=[list(x) for x in masks]
            for m,t in restored:updated[m][t]=True
            bb=[bounds([x for x,k in zip(g,mask) if k],len(g)) for g,mask in zip(grades,updated)]
            if all(bb[w][0]-bb[m][1]>TOL for m in range(len(grades)) if m!=w):return c
    return None

def tests():
    rng=random.Random(102)
    for _ in range(150):
        g=[[rng.choice([0,.25,.5,.75,1]) for t in range(3)] for m in range(3)]
        mask=[[rng.choice([False,True]) for t in range(3)] for m in range(3)]
        w=max(range(3),key=lambda m:sum(g[m]));o=optimal(g,mask,w)
        assert (None if o is None else o['count'])==brute(g,mask,w)
    return 150

# One fixed policy. The selector sees known grades and unavailable identities only.
def select_next(known, missing, models, tasks):
    bb=[bounds(known[m],len(tasks)) for m in range(len(models))]
    incumbent=min(range(len(models)),key=lambda m:(-bb[m][0],models[m]))
    rivals=[m for m in range(len(models)) if m!=incumbent]
    challenger=min(rivals,key=lambda m:(-bb[m][1],models[m]))
    if bb[incumbent][0]-bb[challenger][1]>TOL:return None,incumbent
    queryable=[m for m in (incumbent,challenger) if missing[m]]
    if not queryable:raise ValueError('Cannot strictly certify: fully known unresolved candidates')
    m=min(queryable,key=lambda m:(-len(missing[m]),models[m]))
    t=min(missing[m],key=lambda t:tasks[t])
    return (m,t),None

def adaptive(grades,masks,models,tasks):
    known=[[v for v,k in zip(g,mask) if k] for g,mask in zip(grades,masks)]
    missing=[{t for t,k in enumerate(mask) if not k} for mask in masks]
    log=[]
    while True:
        try:
            slot,w=select_next(known,missing,models,tasks)
        except ValueError:
            return {'queries':len(log),'certified_winner':None,'status':'no_strict_certificate','log':log}
        if slot is None:break
        m,t=slot
        before=[bounds(known[i],len(tasks)) for i in range(len(models))]
        # Only this retrieval sees the held-out truth for the selected identity.
        known[m].append(grades[m][t]);missing[m].remove(t)
        log.append({'model':models[m],'task_id':tasks[t],'grade':grades[m][t],
                    'pre_query_intervals':{name:[float(v) for v in b] for name,b in zip(models,before)},
                    'pre_query_missing_counts':{name:len(missing[i])+(i==m) for i,name in enumerate(models)}})
    bb=[bounds(known[m],len(tasks)) for m in range(len(models))]
    return {'queries':len(log),'certified_winner':models[w], 'winner_lower':float(bb[w][0]), 'largest_other_upper':float(max(bb[m][1] for m in range(len(models)) if m!=w)),'log':log}


def demonstrate(rows):
    result={'target':'Strict maximizer of the equally weighted recorded-grade mean on the declared released roster.',
            'interpretation':'Retrospective masking of available grades. Offline oracle minimum is outcome-informed verification, not a prospective query guarantee. Fixed adaptive selector uses revealed grades and unavailable identities only. No deployment benefit or independent achievement validation.',
            'policy':'Largest lower incumbent, largest upper challenger; query wider interval of those two; lexical model/task tie break.',
            'rules':{}}
    for rule,field,value in [('assistant','last_original_role','assistant'),('native_stop','native_stop_reason','stop'),('exporter','execution_status','completed')]:
        working=[dict(r) for r in rows]
        if rule=='native_stop':
            for r in working:
                if r.get(field) is None:
                    if r.get('last_original_role')=='assistant':
                        raise ValueError('Unknown stop reason on assistant ending')
                    r[field]='__no_assistant_stop_event__'
        models,tasks,g,masks,c=structure(working,field,value,allow_unknown_models=rule=='exporter')
        means=[sum((exact(v) for v in x), Fraction(0))/len(tasks) for x in g]
        winners=[i for i,v in enumerate(means) if max(means)-v<=TOL]
        entry={'models':models,'tasks':len(tasks),'full_roster_maximizers':[models[i] for i in winners],
               'all_omitted_grade_count':sum(not k for mask in masks for k in mask)}
        if len(winners)!=1:
            entry.update(exact_offline_minimum=None,fixed_blinded_policy=adaptive(g,masks,models,tasks),status='no_unique_strict_recorded_winner')
        else:
            w=winners[0];o=optimal(g,masks,w)
            if o is None:raise AssertionError('Unique strict winner has no full-restoration certificate')
            o['winner']=models[w]
            o['by_model']={models[m]:q for m,q in o['by_model'].items()}
            o['disclosures']=[{'model':models[m],'task_id':tasks[t],'grade':g[m][t]} for m,t in o['disclosures']]
            entry.update(exact_offline_minimum=o,fixed_blinded_policy=adaptive(g,masks,models,tasks),status='certified')
        result['rules'][rule]=entry
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ledger', help='Complete released model-task ledger; grades available on [0,1]')
    parser.add_argument('--output', help='Write JSON only to this explicit path; otherwise print to stdout')
    args=parser.parse_args()
    rows=[json.loads(x) for x in Path(args.ledger).read_text().splitlines() if x.strip()]
    data=json.dumps(demonstrate(rows),indent=2,allow_nan=False)+'\n'
    if args.output:Path(args.output).write_text(data)
    else:print(data,end='')

if __name__=='__main__':main()
