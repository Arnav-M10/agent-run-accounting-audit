"""Independent fixed-sample extraction check on local pinned raw inputs.

Requires Python 3 with pyarrow. Read-only source access; no paid inference calls.
Outcome/grade values are copied from native artifacts, not independently regraded.
The 35-record sample tests exact source consistency only, not full pipeline or
whole-release correctness. All published output is metadata; no raw trajectories.
"""
from pathlib import Path
import json,random,hashlib,tarfile,zipfile,argparse
import pyarrow.parquet as pq
parser=argparse.ArgumentParser(description='Fixed 35-record independent source-to-ledger extraction spot check; no grading or inference.')
parser.add_argument('--cmu-data',type=Path,default=Path('data'))
parser.add_argument('--wildclaw-data',type=Path,default=Path('independent_data/wildclaw'))
parser.add_argument('--ledger-root',type=Path,default=Path('run_accounting'))
parser.add_argument('--output',type=Path,help='Metadata-only JSON report; print complete report to stdout if omitted.')
args=parser.parse_args()
D=args.cmu_data; W=args.wildclaw_data; L=args.ledger_root
rng=random.Random(20261007)
report={'seed':20261007,'method':'Sort source identities lexically; use one Python random.Random(20261007), sampling 5 IDs in alphabetical benchmark order, followed by 3 TAR and 2 ZIP pairs from sorted source model/task identities. Choices fixed before inspecting sampled grades or terminal events. Reconstruct fields directly from raw JSONL, parquet trajectory, score archive members, and export headers, without calling corpus adapters.','cmu':[],'wildclaw':[],'mismatches':[],'limitations':['Retained-record sample only; excluded/unreleased CMU records not tested.','CMU execution_status is intentionally unknown in ledger; source benchmark status fields have heterogeneous meanings and were not equated with exporter status.','ZIP exporter status is unavailable at pinned source; null checked without inferring a status.','Checks extraction on 35 selected records only; no independent grading, blind review, full pipeline validation, or whole release correctness claim.']}
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def check(kind,ident,ledger,expected):
 for k,v in expected.items():
  if ledger.get(k)!=v:report['mismatches'].append({'corpus':kind,'identity':ident,'field':k,'expected':v,'ledger':ledger.get(k)})
cmu={x['attempt_id']:x for x in map(json.loads,(L/'cmu_attempts.jsonl').read_text().splitlines())}
for p in sorted(D.glob('*.jsonl')):
 ids=[]
 with p.open() as f:
  for line in f:ids.append(json.loads(line)['id'])
 chosen=set(rng.sample(sorted(ids),min(5,len(ids))))
 with p.open() as f:
  for line in f:
   x=json.loads(line)
   if x['id'] not in chosen:continue
   msgs=x['messages']; last=msgs[-1] if msgs else {}
   expected={'attempt_id':x['id'],'benchmark':x['benchmark'],'model':x['source_model'],'domain':x['domain'],'task_id':str(x['task_id']),'pass':x['pass'],'native_score':x['reward'],'last_original_role':last.get('role'),'retention':'retained','score_available':True,'execution_status':None}
   check('cmu',x['id'],cmu[x['id']],expected)
   report['cmu'].append({'id':x['id'],'source_file':p.name,'raw_line_sha256':sha(line.encode()),'fields_compared':sorted(expected),'final_event_has_native_stop': 'stopReason' in last,'native_stop_ledger_availability':'not exported','sample_field_match': all(cmu[x['id']].get(k)==v for k,v in expected.items())})
frame=pq.read_table(W/'train.parquet',columns=['model_name','task_id']).to_pylist()
slugs={'Claude Fable 5':'claude_fable5','Claude Opus 4.8 Thinking':'claude_opus_4_8_thinking','GLM 5.2':'glm52','GPT-5.6 Sol':'gpt56_sol','Grok 4.5':'grok45','Hy3':'hy3','Intern-S2-Preview-397B':'intern-s2-preview-397b','Kimi K2.7 Code':'kimi_k2.7_code','Kimi K3':'kimi_k3','Muse Spark 1.1':'muse_spark_1_1','Qwen3.8 Max':'qwen3.8-max','Qwen3.8-27B (vLLM)':'qwen3.8-27b-vllm'}
zipmodels={'Qwen3.8 Max','Qwen3.8-27B (vLLM)'}
selected=[]
for fmt,n in [('tar.gz',3),('zip',2)]:
 pool=sorted((x['model_name'],x['task_id']) for x in frame if (x['model_name'] in zipmodels)==(fmt=='zip'))
 selected.extend((m,t,fmt) for m,t in rng.sample(pool,n))
report['selection_order']=[{'model':m,'task_id':t,'format':fmt} for m,t,fmt in selected]
wledger={(x['model'],x['task_id']):x for x in map(json.loads,(L/'wildclaw_released_pairs.jsonl').read_text().splitlines())}
report['input_hashes']={'train.parquet':file_sha(W/'train.parquet'),'cmu_attempts.jsonl':file_sha(L/'cmu_attempts.jsonl'),'wildclaw_released_pairs.jsonl':file_sha(L/'wildclaw_released_pairs.jsonl')}
report['input_hashes'].update({p.name:file_sha(p) for p in sorted(D.glob('*.jsonl'))})
for m,t,fmt in selected:
 row=pq.read_table(W/'train.parquet',filters=[('model_name','=',m),('task_id','=',t)]).to_pylist()[0]
 terminal=json.loads(row['trajectory'])[-1]
 ap=W/('output_'+slugs[m]+'.'+fmt)
 if fmt=='zip':
  with zipfile.ZipFile(ap) as z:
   paths=[p for p in z.namelist() if p.endswith('/score.json') and t in p.split('/')]
   assert len(paths)==1; raw=z.read(paths[0])
 else:
  with tarfile.open(ap) as z:
   paths=[p for p in z.getmembers() if p.isfile() and p.name.endswith('/score.json') and t in p.name.split('/')]
   assert len(paths)==1; raw=z.extractfile(paths[0]).read()
 score=json.loads(raw)['overall_score']; header=None; status=None
 if fmt=='tar.gz':
  hp=W/'sessions'/slugs[m]/(t+'.jsonl')
  headerline=hp.open().readline();header=json.loads(headerline)
  assert header['task_id']==t;status=header['trace_status']
 expected={'model':row['model_name'],'task_id':row['task_id'],'native_score':score,'score_available':True,'last_original_role':terminal.get('role'),'execution_status':status,'native_stop_reason':terminal.get('stopReason'),'retention':'released'}
 ledger=wledger[(m,t)];check('wildclaw',[m,t],ledger,expected)
 if ('native_stop_reason' in ledger)!=('stopReason' in terminal):report['mismatches'].append({'corpus':'wildclaw','identity':[m,t],'field':'native_stop_presence'})
 out={'model':m,'task_id':t,'archive':ap.name,'format':fmt,'score_member':paths[0] if fmt=='zip' else paths[0].name,'score_json_sha256':sha(raw),'trajectory_utf8_sha256':sha(row['trajectory'].encode()),'fields_compared':sorted(expected),'native_stop_presence_match':('native_stop_reason' in ledger)==('stopReason' in terminal),'sample_field_match':all(ledger.get(k)==v for k,v in expected.items())}
 if header:out['session_header_sha256']=sha(headerline.encode())
 report['wildclaw'].append(out)
 if ap.name not in report['input_hashes']:report['input_hashes'][ap.name]=file_sha(ap)
report['summary']={'cmu_retained':len(report['cmu']),'cmu_benchmarks':6,'wildclaw_pairs':len(report['wildclaw']),'wildclaw_tar_pairs':3,'wildclaw_zip_pairs':2,'total_records':len(report['cmu'])+len(report['wildclaw']),'field_mismatches':len(report['mismatches']),'cmu_native_stop_present':sum(x['final_event_has_native_stop'] for x in report['cmu'])}
payload=json.dumps(report,indent=2,sort_keys=True)+'\n'
if args.output:
 args.output.write_text(payload)
 print(json.dumps({'summary':report['summary'],'selection_order':report['selection_order'],'mismatches':report['mismatches']},indent=2))
else:
 print(payload,end='')
raise SystemExit(1 if report['mismatches'] else 0)
