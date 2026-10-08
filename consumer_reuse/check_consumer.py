"""Check released Messier General-AgentBench populations and replay its task means.
No downloads or model calls. Accepts full records JSONL or extracted CMU rows.
"""
import argparse, collections, csv, hashlib, json
from pathlib import Path
MODELS = {'DeepSeek-R1':'deepseek-r1','DeepSeek-V3.2':'deepseek-v3-2','Gemini-2.5-Flash':'gemini-2-5-flash','Qwen3-235B':'qwen-3-235b-a22b','Qwen3-Next':'qwen-3-next'}
DOMAINS = {'mathhay','browsecomp','webvoyager','mcpbench'}
def read(path):
    with open(path) as f:
        for line in f:
            if line.strip(): yield json.loads(line)
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--consumer',required=True);p.add_argument('--ledger',required=True);p.add_argument('--out',required=True);args=p.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    source=list(read(args.ledger)); src=collections.defaultdict(list); original={}
    for r in source:
        b=r['domain'] if r['benchmark']=='search' else r['benchmark']
        if r['retention']=='retained' and b in DOMAINS:
            k=(b,r['task_id'],MODELS[r['model']]);src[k].append(r['native_score']);original[(*k,r['pass']-1)]=r
    consumer=collections.defaultdict(list);trials=collections.defaultdict(list);counts=collections.Counter();verifiers=collections.Counter();seen=set();unmapped=0;direct_mismatches=0;result_mismatches=0
    for r in read(args.consumer):
        if r.get('agent_scaffold')!='general-agentbench':continue
        b=r['benchmark']
        if b not in DOMAINS:continue
        if r['record_type']=='verifier_result':verifiers[b]+=1;continue
        if r['record_type']!='trial_result':continue
        k=(b,r['task_id'],r['agent_model']);counts[b]+=1;consumer[k].append(r['metadata']['source_reward']);trials[k].append(r['trial']);full=(*k,r['trial']);
        if full in seen:raise ValueError('Duplicate consumer trial identity')
        seen.add(full)
        if full not in original:unmapped+=1
        elif abs(original[full]['native_score']-r['metadata']['source_reward'])>1e-10:direct_mismatches+=1
        reward=r['metadata']['source_reward'];expected=int(reward>=5) if b=='mcpbench' else int(reward==1)
        if expected!=r['result']:result_mismatches+=1
    unequal=[]
    for k in set(src)|set(consumer):
        a=sorted(src[k]);b=sorted(consumer[k])
        if len(a)!=len(b) or any(abs(x-y)>1e-10 for x,y in zip(a,b)):unequal.append(k)
    summary={'consumer_dataset_revision':'42e03cf072039e1428ad1dc970711035cfd24a5e','source_code_revision':'2cf0d31ba6ee8e04714dc6c782c971f1b1a49b53','cmu_revision':'88e2af82c116a9a57f29be6f21b9924da081c2bd','consumer_input_sha256':sha(args.consumer),'cmu_ledger_sha256':sha(args.ledger),'trial_counts':dict(counts),'verifier_counts':dict(verifiers),'source_groups':len(src),'consumer_groups':len(consumer),'groupwise_reward_multiset_mismatches':len(unequal),'dense_consumer_trial_ids':all(sorted(v)==list(range(len(v))) for v in trials.values()),'naive_original_pass_keys_absent':len(set(original)-seen),'naive_consumer_keys_unmapped':unmapped,'naive_direct_reward_mismatches':direct_mismatches,'trial_result_mapping_mismatches':result_mismatches,'boundary':'Groupwise retained-grade identity; dense consumer trial numbering prevents direct source pass identity. Historical paper-producing revisions unknown.'}
    (out/'consumer_check.json').write_text(json.dumps(summary,indent=2)+'\n')
    groups=collections.defaultdict(list)
    for r in source:
        if r['benchmark']=='search':groups[(r['model'],r['domain'],r['task_id'])].append(r)
    by=collections.defaultdict(list)
    for (m,d,t),rr in groups.items():
        kept=[r for r in rr if r['retention']=='retained']
        if not kept:continue
        if len(rr)!=4 or not all(r['score_available'] for r in rr):raise ValueError('Supported task lacks complete recorded grades')
        by[(m,d)].append((sum(r['native_score'] for r in kept)/len(kept),sum(r['native_score'] for r in rr)/4,len(kept)))
    rows=[]
    for (m,d),vs in sorted(by.items()):
        n=len(vs);a=sum(x[0] for x in vs)/n;b=sum(x[1] for x in vs)/n
        rows.append({'model':m,'domain':d,'messier_imported_domain':d in {'browsecomp','webvoyager'},'supported_tasks':n,'retained_runs':sum(x[2] for x in vs),'observed_trial_task_mean':a,'four_recorded_grade_task_mean_same_tasks':b,'difference':a-b})
    with (out/'reduction_replay.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps(summary,indent=2))
    if unequal or result_mismatches:raise SystemExit('Consumer population/results differ')
if __name__=='__main__':main()
