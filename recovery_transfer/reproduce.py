"""Fixed retrospective interval controls; no inference or network calls."""
import csv
import hashlib
import io
import json
import random
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from winner_recovery import TOL, exact, bounds, optimal, select_next
from mask_reference_audit import structure
from recovery_stress import summary, retrieve_in_order

METHODS = ('selector_blind', 'active_candidate', 'challenger_focused', 'lexicographic', 'randomized', 'oracle', 'restore_all')
INPUTS = ['run_accounting/wildclaw_released_pairs.jsonl', 'hal_transfer/hal_task_ledger.jsonl', 'hal_mixed_transfer/hal_mixed_ledger.jsonl', 'hal_transfer/source_manifest.json', 'hal_mixed_transfer/source_manifest.json', 'hal_mixed_transfer/selection_plan.json', 'winner_recovery.py', 'mask_reference_audit.py', 'recovery_stress.py']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]

def load_rosters():
    wild = read(ROOT/INPUTS[0])
    models, tasks, grades, _, _ = structure(wild, 'last_original_role', 'assistant')
    assert (len(models),len(tasks),len(wild)) == (12,60,720)
    rosters = {'wild_original': (models,tasks,grades)}
    allrows = read(ROOT/INPUTS[1])+read(ROOT/INPUTS[2])
    mixed = {r['run_id'] for r in read(ROOT/INPUTS[2])}
    manifests = [json.loads((ROOT/p).read_text()) for p in INPUTS[3:5]]
    expected = {s['filename'].removesuffix('_UPLOAD.zip'):s['sha256'] for manifest in manifests for s in manifest['sources']}
    assert len(expected)==5
    assert {r['run_id'] for r in allrows} == set(expected)
    assert len(allrows)==225
    seen=set(); roster={}
    for r in allrows:
        key=(r['run_id'],r['task_id'])
        assert key not in seen; seen.add(key)
        assert r['score_available'] is True and r['score_scale']==[0,1]
        assert 0<=exact(r['native_score'])<=1
        assert r['source_archive_sha256']==expected[r['run_id']]
        assert r['benchmark']=='corebench_hard'
        assert r['source_grade_policy'].startswith('all_task_questions_correct; parse_error assigns zero') or r['source_grade_policy']=='archived successful_tasks/failed_tasks labels; no raw grading records'
        assert r['native_score']==int(r['source_outcome']=='success')
        roster.setdefault(r['run_id'],{})[r['task_id']]=r['native_score']
    common=set.intersection(*(set(x) for x in roster.values()))
    assert len(common)==45 and all(set(x)==common for x in roster.values())
    tasks=sorted(common)
    for label,ids in [('hal_all_five',set(roster)),('hal_size_selected_three',mixed)]:
        ids=sorted(ids); rosters[label]=(ids,tasks,[[roster[m][t] for t in tasks] for m in ids])
    selected=json.loads((ROOT/INPUTS[5]).read_text())['selected']
    assert mixed=={s['path'].removesuffix('_UPLOAD.zip') for s in selected}
    return rosters

def independent_certificate(grades,masks,restored):
    """Independent reconstruction from decimal numerators; no bounds import."""
    known=[list(mask) for mask in masks]
    assert len(restored)==len(set(restored))
    for m,t in restored:
        assert not known[m][t]; known[m][t]=True
    n=len(grades[0]); intervals=[]
    for g,k in zip(grades,known):
        total=sum((Fraction(str(v)) for v,keep in zip(g,k) if keep),Fraction(0))
        intervals.append((total/n,(total+sum(not keep for keep in k))/n))
    winners=[m for m,(lower,_) in enumerate(intervals) if all(lower-upper>Fraction(1,10**12) for j,(_,upper) in enumerate(intervals) if j!=m)]
    assert len(winners)<=1
    return winners[0] if winners else None

def controlled(grades,masks,models,tasks,method):
    known=[[v for v,k in zip(g,mask) if k] for g,mask in zip(grades,masks)]
    missing=[{t for t,k in enumerate(mask) if not k} for mask in masks]
    restored=[]
    while True:
        if method=='selector_blind':
            try: slot,w=select_next(known,missing,models,tasks)
            except ValueError: return restored,None
            if slot is None:return restored,w
        else:
            bb=[bounds(k,len(tasks)) for k in known]
            incumbent=min(range(len(models)),key=lambda m:(-bb[m][0],models[m]))
            rival=min((m for m in range(len(models)) if m!=incumbent),key=lambda m:(-bb[m][1],models[m]))
            if bb[incumbent][0]-bb[rival][1]>TOL:return restored,incumbent
            if method=='active_candidate':
                candidates=[m for m in range(len(models)) if bb[m][1]>=bb[incumbent][0]-TOL and missing[m]]
                if not candidates:return restored,None
                m=min(candidates,key=lambda m:models[m])
            else:
                candidates=[m for m in (rival,incumbent) if missing[m]]
                if not candidates:return restored,None
                m=candidates[0]
            slot=(m,min(missing[m],key=lambda t:tasks[t]))
        m,t=slot
        # Only the selected cell is accessed after the decision.
        known[m].append(grades[m][t]); missing[m].remove(t); restored.append(slot)

def experiment():
    records=[]; results={}
    for label,(models,tasks,grades) in load_rosters().items():
        means=[sum((exact(v) for v in g),Fraction(0))/len(tasks) for g in grades]
        full=independent_certificate(grades,[[True]*len(tasks) for _ in models],[])
        maxima=[i for i,v in enumerate(means) if max(means)-v<=TOL]
        results[label]={'model_or_run_count':len(models),'task_count':len(tasks),'cell_count':len(models)*len(tasks),'full_mean_maximizer_count':len(maxima),'strict_full_winner_exists':full is not None,'rates':{}}
        for ri,rate in enumerate((.1,.25,.5)):
            group=[]
            for seed in range(30):
                ms=2026100800+1000*ri+seed; rs=2026101800+1000*ri+seed
                rng=random.Random(ms)
                masks=[[rng.random()>=rate for _ in tasks] for _ in models]
                slots=[(m,t) for m,mask in enumerate(masks) for t,k in enumerate(mask) if not k]
                record={'roster':label,'rate':rate,'seed_index':seed,'mask_seed':ms,'retrieval_seed':rs,'mask_sha256':hashlib.sha256(json.dumps(masks,separators=(',',':')).encode()).hexdigest(),'omitted_count':len(slots),'full_mean_maximizer_count':len(maxima),'initial_certificate':int(independent_certificate(grades,masks,[]) is not None)}
                outcomes={}
                for method in METHODS:
                    if method in METHODS[:3]: disclosures,w=controlled(grades,masks,models,tasks,method)
                    elif method in ('lexicographic','randomized'):
                        order=slots.copy()
                        if method=='randomized':random.Random(rs).shuffle(order)
                        disclosures,w=retrieve_in_order(grades,masks,order)
                    elif method=='restore_all': disclosures,w=slots,full
                    else:
                        o=optimal(grades,masks,full) if full is not None else None
                        if o is None:
                            outcomes[method]=(None,None);record[method+'_cost']=None;record[method+'_certificate']=0;continue
                        disclosures,w=o['disclosures'],full
                    actual=independent_certificate(grades,masks,disclosures)
                    assert actual==w and (w is None or w==full)
                    outcomes[method]=(len(disclosures),w)
                    record[method+'_cost']=len(disclosures);record[method+'_certificate']=int(w is not None)
                if outcomes['oracle'][0] is not None:
                    assert all(outcomes['oracle'][0]<=outcomes[m][0] for m in METHODS if m!='oracle')
                records.append(record);group.append(record)
            rates={'all_case_count':30,'full_tie_cases':30 if full is None else 0,'oracle_null_cases':sum(r['oracle_cost'] is None for r in group),'initial_certificate_cases':sum(r['initial_certificate'] for r in group),'methods':{},'paired_selector_minus_comparator':{}}
            for method in METHODS:
                costs=[r[method+'_cost'] for r in group if r[method+'_cost'] is not None]
                rates['methods'][method]={'certificate_cases':sum(r[method+'_certificate'] for r in group),'certificate_denominator_all_cases':30,'costs_nonnull':summary(costs) if costs else None}
            for method in METHODS[1:]:
                pairs=[(r['selector_blind_cost'],r[method+'_cost']) for r in group if r[method+'_cost'] is not None]
                rates['paired_selector_minus_comparator'][method]={'nonnull_cases':len(pairs),'lower':sum(a<b for a,b in pairs),'equal':sum(a==b for a,b in pairs),'higher':sum(a>b for a,b in pairs),'difference':summary([a-b for a,b in pairs]) if pairs else None}
            results[label]['rates'][str(rate)]=rates
    return results,records

def encoded(results,records):
    result=json.dumps(results,sort_keys=True,indent=2,allow_nan=False)+'\n'
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    return result,stream.getvalue()

def main():
    first=encoded(*experiment()); second=encoded(*experiment()); assert first==second
    (HERE/'results.json').write_text(first[0]); (HERE/'per_case.csv').write_text(first[1])
    manifest={p:sha(ROOT/p) for p in INPUTS}
    manifest.update({'recovery_transfer/PLAN.md':sha(HERE/'PLAN.md'),'recovery_transfer/reproduce.py':sha(Path(__file__))})
    (HERE/'source_hash_manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    verification={'case_count':270,'method_count':7,'deterministic_two_fresh_replays_byte_identical':True,'independent_final_certificate_reconstruction':True,'false_certificate_count':0,'all_source_run_task_identities_unique':True,'hal_common_task_count':45,'distinct_hal_archives':5,'all_cases_retained':True,'no_raw_archive_rows_published':True}
    (HERE/'verification.json').write_text(json.dumps(verification,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:{r:{m:d['costs_nonnull']['mean'] if d['costs_nonnull'] else None for m,d in v['methods'].items()} for r,v in x['rates'].items()} for k,x in json.loads(first[0]).items()},indent=2))

if __name__=='__main__':main()
