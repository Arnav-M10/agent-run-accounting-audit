"""Replay pinned Messier terminal CMU search frontier reduction; no inference.
See PLAN.md for the frozen estimand and missing-data rules. Standard library only.
"""
import argparse, collections, csv, hashlib, json
from fractions import Fraction
from pathlib import Path

MODELS = {'DeepSeek-R1':'deepseek-r1','DeepSeek-V3.2':'deepseek-v3-2','Gemini-2.5-Flash':'gemini-2-5-flash','Qwen3-235B':'qwen-3-235b-a22b','Qwen3-Next':'qwen-3-next'}
DOMAINS = ('browsecomp','webvoyager')
def read(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def unique(rows, key):
    keys=[key(r) for r in rows]
    assert len(keys)==len(set(keys)), 'duplicate keys'
def f(x): return float(x)
def value(x): return {'value':float(x),'exact':str(x)}
def main():
    p=argparse.ArgumentParser();p.add_argument('--consumer',required=True);p.add_argument('--ledger',required=True);p.add_argument('--slots',required=True);p.add_argument('--manifest',required=True);p.add_argument('--source-root',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    allsrc=read(a.ledger);allslt=read(a.slots)
    src=[r for r in allsrc if r['benchmark']=='search' and r['domain'] in DOMAINS]
    slots=[r for r in allslt if r['domain'] in DOMAINS]
    cons=[r for r in read(a.consumer) if r.get('agent_scaffold')=='general-agentbench' and r['benchmark'] in DOMAINS and r['record_type']=='trial_result']
    unique(src,lambda r:(r['domain'],r['task_id'],r['model'],r['pass']))
    unique(slots,lambda r:(r['domain'],r['task_id'],r['model'],r['pass']))
    unique(cons,lambda r:(r['benchmark'],r['task_id'],r['agent_model'],r['trial']))
    skeys={(r['domain'],r['task_id'],r['model'],r['pass']):r for r in slots}
    source=collections.defaultdict(list);kept=collections.defaultdict(list);consumer=collections.defaultdict(list)
    for r in src:
        k=(r['domain'],r['task_id'],r['model']);source[k].append(r)
        sl=skeys[(*k,r['pass'])]
        assert sl['observed_attempt_id']==r['attempt_id'] and sl['coverage']=='released'
        assert r['score_available'] and r['native_score'] in (0,1)
        if r['retention']=='retained':kept[k].append(Fraction(r['native_score']))
    reverse={v:k for k,v in MODELS.items()}
    for r in cons:
        assert r['result']==int(r['metadata']['source_reward']==1)
        consumer[(r['benchmark'],r['task_id'],reverse[r['agent_model']])].append(Fraction(r['result']))
    assert set(kept)==set(consumer)
    assert all(sorted(kept[k])==sorted(consumer[k]) for k in kept)
    manifest=json.loads(Path(a.manifest).read_text());pins=[]
    for item in manifest['source_files']:
        rel=item['url'].split(manifest['consumer_source_revision']+'/')[1]
        path=Path(a.source_root)/rel
        assert sha(path)==item['sha256'],str(path)
        pins.append({'path':rel,'sha256':item['sha256']})
    coverage=[];results=[]
    for domain in DOMAINS:
        tasks=sorted({r['task_id'] for r in slots if r['domain']==domain})
        for task in tasks:
            assert {(r['model'],r['pass']) for r in slots if r['domain']==domain and r['task_id']==task}=={(m,i) for m in MODELS for i in range(1,5)}
        full=[t for t in tasks if all((domain,t,m) in consumer for m in MODELS)]
        for m in MODELS:
            rr=[r for r in src if r['domain']==domain and r['model']==m]
            coverage.append({'domain':domain,'model':m,'declared_tasks':len(tasks),'retained_supported_tasks':sum((domain,t,m) in consumer for t in tasks),'absent_retained_model_task_groups':sum((domain,t,m) not in consumer for t in tasks),'released_grades':len(rr),'retained_grades':sum(r['retention']=='retained' for r in rr),'known_removed_grades':sum(r['retention']!='retained' for r in rr),'unknown_grades':len(tasks)*4-len(rr)})
        for name,pop in [('all_declared_tasks',tasks),('all_models_retained_supported_tasks',full)]:
            inherited=[];low=[];high=[];changes_lo=[];changes_hi=[];unknown=0;unobserved_tasks=0;retained_ties=0;four_pass_lower_ties=0;four_pass_upper_ties=0
            for t in pop:
                retained_means=[sum(consumer[(domain,t,m)])/len(consumer[(domain,t,m)]) for m in MODELS if (domain,t,m) in consumer]
                if not retained_means:unobserved_tasks+=1;raise ValueError('No retained candidate: bounded retained frontier required')
                inherited.append(max(retained_means));retained_ties+=retained_means.count(max(retained_means))>1;lo=[];hi=[]
                for m in MODELS:
                    rr=source[(domain,t,m)];n=4-len(rr);unknown+=n
                    assert 0<=n<=4
                    total=sum(Fraction(r['native_score']) for r in rr)
                    lo.append(total/4);hi.append((total+n)/4)
                four_pass_lower_ties+=lo.count(max(lo))>1;four_pass_upper_ties+=hi.count(max(hi))>1
                low.append(max(lo));high.append(max(hi));changes_lo.append(inherited[-1]-high[-1]);changes_hi.append(inherited[-1]-low[-1])
            n=len(pop);rmean=sum(inherited)/n;lmean=sum(low)/n;hmean=sum(high)/n
            results.append({'domain':domain,'population':name,'task_count':n,'excluded_tasks_relative_to_declared':len(tasks)-n,'tasks_without_any_retained_candidate':unobserved_tasks,'unknown_four_pass_grades':unknown,'tasks_with_tied_retained_maximum':retained_ties,'tasks_with_tied_four_pass_lower_maximum':four_pass_lower_ties,'tasks_with_tied_four_pass_upper_maximum':four_pass_upper_ties,'retained_frontier':value(rmean),'four_pass_frontier_lower':value(lmean),'four_pass_frontier_upper':value(hmean),'difference_lower':value(rmean-hmean),'difference_upper':value(rmean-lmean),'tasks_with_definite_change':sum(l>0 or h<0 for l,h in zip(changes_lo,changes_hi)),'tasks_with_possible_change':sum(l!=0 or h!=0 for l,h in zip(changes_lo,changes_hi)),'maximum_task_change_lower':value(max(changes_lo)),'maximum_task_change_upper':value(max(changes_hi))})
    result={'scope':'Terminal all-five-model source-defined max-after-task-mean reduction restricted to CMU imported search; not full Messier quarterly frontier or IRT.','source_data_revision':manifest['consumer_revision'],'source_code_revision':manifest['consumer_source_revision'],'cmu_revision':manifest['cmu_revision'],'historical_generating_revision':'unknown','identity_boundary':'Retained grade multisets per domain/task/model; no pass/event identity claim. Extracted metadata omits model_date and agent_id; terminal eligibility and one builder agent per model are source-defined scope conditions.','checks':{'unique_source_attempt_keys':True,'unique_declared_slot_keys':True,'unique_consumer_trial_keys':True,'source_slot_attempt_identity_match':True,'retained_grade_group_multiset_match':True,'search_binary_mapping_match':True,'verified_source_file_hashes':pins,'consumer_search_trials':len(cons),'retained_search_groups':len(consumer),'declared_imported_search_tasks':sum(len({r['task_id'] for r in slots if r['domain']==d}) for d in DOMAINS),'declared_all_search_tasks_including_nonimported_mind2web':len({(r['domain'],r['task_id']) for r in allslt})},'input_sha256':{name:sha(path) for name,path in [('consumer_metadata',a.consumer),('source_ledger',a.ledger),('declared_slots',a.slots),('consumer_manifest',a.manifest),('frozen_plan',out/'PLAN.md')]},'missing_grade_bound_rule':'Each unreleased grade independently ranges from 0 to 1; task frontier monotonicity makes endpoints exact. Known removed grades are included, never zero-imputed.','coverage':coverage,'frontiers':results}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    with (out/'coverage.csv').open('w') as file:
        w=csv.DictWriter(file,fieldnames=list(coverage[0]));w.writeheader();w.writerows(coverage)
    print(json.dumps(results,indent=2))
if __name__=='__main__':main()
