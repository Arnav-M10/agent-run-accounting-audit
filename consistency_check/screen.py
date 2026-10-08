import json,collections,itertools,math,argparse,csv,hashlib
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--ledger-dir',type=Path,default=Path(__file__).resolve().parent.parent/'run_accounting')
parser.add_argument('--out-dir',type=Path,default=Path(__file__).resolve().parent)
args=parser.parse_args()
root=args.ledger_dir
args.out_dir.mkdir(parents=True,exist_ok=True)
all_attempts=[json.loads(l) for l in (root/'cmu_attempts.jsonl').open()]
A=[r for r in all_attempts if r['benchmark']=='search']
slots=[json.loads(l) for l in (root/'cmu_search_slots.jsonl').open()]
# Declared fixed four-pass binary roster; reject incompatible metadata.
slot_key=lambda r:(r['model'],r['domain'],r['task_id'],r['pass'])
if len(slots)!=3980 or len({slot_key(r) for r in slots})!=3980:raise ValueError('Expected 3980 distinct scheduled slots')
if len(A)!=3979 or len({slot_key(r) for r in A})!=3979:raise ValueError('Expected 3979 distinct available grades')
if not {slot_key(r) for r in A} <= {slot_key(r) for r in slots}:raise ValueError('Grade outside declared roster')
if any(r['native_score'] not in (0,1) or r.get('score_available') is not True for r in A):raise ValueError('Binary recorded grades required')
slot_groups=collections.defaultdict(set)
for r in slots:slot_groups[(r['model'],r['domain'],r['task_id'])].add(r['pass'])
if len(slot_groups)!=995 or any(v!={1,2,3,4} for v in slot_groups.values()):raise ValueError('Four planned pass positions per group required')
key=lambda a:(a['model'],a['domain'],a['task_id'])
G=collections.defaultdict(list)
for a in A:G[key(a)].append(a)
for a in slots:G[key(a)]
rows=[]
C=lambda s,k:(2*s/k-1)**2
for (m,d,t),a in G.items():
 r=[x for x in a if x['retention']=='retained'];s=sum(x['native_score'] for x in r);k=len(r); fulls=sum(x['native_score'] for x in a);n=len(a)
 full=[C(fulls+j,4) for j in range(5-n)]
 vals=[C(s+j,4) for j in range(5-k)]
 row=dict(model=m,domain=d,task=t,n=n,k=k,s=s,full_successes=fulls,full_lo=min(full),full_hi=max(full),retained_C=C(s,k) if k else None,retained_U=(k*C(s,k)-1)/(k-1) if k>1 else None,missing_lo=min(vals),missing_hi=max(vals))
 if n==4 and k>0:row['random_thin_C']=C(fulls,4)+(1-C(fulls,4))*(4-k)/(3*k)
 rows.append(row)
def mean(rs,field):
 v=[r[field] for r in rs if r.get(field) is not None];return sum(v)/len(v) if v else None
def summ(rs):
 supported=[r for r in rs if r['k']];complete=[r for r in rs if r['k']==4];inc=[r for r in rs if 0<r['k']<4];known_supported=[r for r in supported if r['n']==4]
 return dict(N=len(rs),k_counts=dict(collections.Counter(r['k'] for r in rs)),full_recorded_bounds=[mean(rs,'full_lo'),mean(rs,'full_hi')],available_retained=mean(supported,'retained_C'),complete_only=mean(complete,'retained_C'),full_on_retained_support=[mean(supported,'full_lo'),mean(supported,'full_hi')],incomplete_available=mean(inc,'retained_C'),incomplete_full_bounds=[mean(inc,'full_lo'),mean(inc,'full_hi')],random_thin_known_supported=mean(known_supported,'random_thin_C'),actual_known_supported=mean(known_supported,'retained_C'),retained_missing_bounds=[mean(rs,'missing_lo'),mean(rs,'missing_hi')],always_fail_full_known=sum(r['n']==4 and r['full_successes']==0 for r in rs),always_success_full=sum(r['full_successes']==4 for r in rs),full_counts=dict(collections.Counter(str((r['n'],r['full_successes'])) for r in rs)))
out={'provenance':{'target':'task-weighted recorded four-pass outcome consistency','analysis_timing':'post hoc, outcome-informed','metric_source':'https://arxiv.org/html/2602.16666v3','ledger_sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['cmu_attempts.jsonl','cmu_search_slots.jsonl']}},'overall':summ(rows),'models':{m:summ([r for r in rows if r['model']==m]) for m in sorted({r['model'] for r in rows})},'cells':{m+' / '+d:summ([r for r in rows if r['model']==m and r['domain']==d]) for m,d in sorted({(r['model'],r['domain']) for r in rows})}}
(args.out_dir/'results.json').write_text(json.dumps(out,indent=2))
(args.out_dir/'groups.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
for name,z in [('overall',out['overall']),*out['models'].items(),*out['cells'].items()]:
 print(name,'N',z['N'],'k',z['k_counts'],'full',z['full_recorded_bounds'],'available',z['available_retained'],'complete',z['complete_only'],'fullsupport',z['full_on_retained_support'],'bounds',z['retained_missing_bounds'],'thin',z['random_thin_known_supported'])

with (args.out_dir/'all_cells.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator="\n"); w.writerow(['cell','N','supported','full_C_lower','full_C_upper','retained_C','complete_C','same_support_full_C_lower','same_support_full_C_upper','uniform_thinned_C'])
 for name,z in out['cells'].items():w.writerow([name,z['N'],z['N']-z['k_counts'].get(0,0),*z['full_recorded_bounds'],z['available_retained'],z['complete_only'],*z['full_on_retained_support'],z['random_thin_known_supported']])
