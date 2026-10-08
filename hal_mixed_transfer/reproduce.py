#!/usr/bin/env python3
"""Replay three size-selected public HAL archives without any agent execution."""
import argparse,base64,collections,hashlib,json,math,subprocess,tempfile,zipfile
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from summarize_ledger import summarize
from check_ledger import check
ROOT=Path(__file__).resolve().parent
EVAL_SHA='7d04be1e8fa92a6db0c535e490708dbb7a3605ff88ff05ea5d19e3ee4fa0090f'
DECRYPT_COMMIT='16bb03ebc11577fb5ea6dc8bb6c968387085e6aa'
DECRYPT_HASHES={'decrypt.py':'0406a8c44b466d390e69a72fd585c0e905babbae5e4150dcf71357287f2afcfc','json_encryption.py':'8aa91ca6ddb67005d276159a280e566cd3e3a2327247bb96136c0de0ab4ac895'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def get(cache,name,url,digest,size=None):
 p=cache/name
 if not p.exists():subprocess.run(['curl','--fail','--location','--silent','--show-error','--max-time','60',url,'-o',str(p)],check=True)
 assert sha(p)==digest and (size is None or p.stat().st_size==size),name
 return p

def decode(p):
 with zipfile.ZipFile(p) as z:
  assert len(z.namelist())==1;e=json.loads(z.read(z.namelist()[0]))
 key=PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,salt=base64.b64decode(e['salt']),iterations=480000).derive(b'hal1234')
 return json.loads(Fernet(base64.urlsafe_b64encode(key)).decrypt(base64.b64decode(e['encrypted_data'])))
def write(n,x):(ROOT/n).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def run(cache):
 cache.mkdir(parents=True,exist_ok=True);plan=json.loads((ROOT/'selection_plan.json').read_text());rows=[];details=[];sources=[];universes=[]
 for n,d in DECRYPT_HASHES.items():get(cache,'official_'+n,'https://raw.githubusercontent.com/princeton-pli/hal-harness/'+DECRYPT_COMMIT+'/hal/utils/'+n,d)
 for r in plan['selected']:
  url='https://huggingface.co/datasets/agent-evals/hal_traces/resolve/'+plan['dataset_revision']+'/'+r['path'];p=get(cache,r['path'],url,r['lfs']['oid'],r['size']);x=decode(p);ev=x['raw_eval_results'];logs=x['raw_logging_results'];res=x['results'];runid=x['config']['run_id'];commit=x['git_info']['commit'];eurl='https://raw.githubusercontent.com/princeton-pli/hal-harness/'+commit+'/hal/benchmarks/corebench.py'
  code=get(cache,'corebench_'+commit+'.py',eurl,EVAL_SHA);assert 'json.loads(solution)' in code.read_text() and '"error": str(e)' in code.read_text()
  passes=set(res['successful_tasks']);fails=set(res['failed_tasks']);ids=set(ev)
  assert len(ids)==45 and not passes&fails and passes|fails==ids
  assert len(res['successful_tasks'])==len(passes) and len(res['failed_tasks'])==len(fails)
  assert math.isclose(res['accuracy'],len(passes)/45,abs_tol=1e-12);universes.append(ids)
  mapped=collections.defaultdict(list)
  for q in logs:
   t=q.get('weave_task_id') or q.get('attributes',{}).get('weave_task_id');assert t in ids;mapped[t].append(q)
  assert set(mapped)==ids
  for t in sorted(ids):
   v=ev[t];parse=bool(v.get('error'));score=int(t in passes)
   assert v['total_written_questions']+v['total_vision_questions']>0
   native=int(v['correct_written_answers']==v['total_written_questions'] and v['correct_vision_answers']==v['total_vision_questions']);assert native==score
   if parse:assert score==0 and v['error']=='Expecting value: line 1 column 1 (char 0)'
   ex=[]
   for q in mapped[t]:
    if q.get('exception'):
     e=json.loads(q['exception']) if isinstance(q['exception'],str) else q['exception'];ex.append(e['type'])
   rows.append({'run_id':runid,'task_id':t,'benchmark':'corebench_hard','native_score':score,'score_scale':[0,1],'score_available':True,'source_outcome':'success' if score else 'failure','parse_error_present':parse,'logged_exception_present':bool(ex),'recorded_exception_types':sorted(set(ex)),'mapped_call_count':len(mapped[t]),'status_coverage':'all_evaluation_rows_and_all_archived_calls_joined','execution_status':'recorded_call_exception' if ex else 'no_exception_in_archived_calls','parse_status':'recorded_parse_error' if parse else 'no_error_in_evaluation_record','source_archive_sha256':r['lfs']['oid'],'source_grade_policy':'all_task_questions_correct; parse_error assigns zero','source_evaluator_commit':commit})
  rr=[q for q in rows if q['run_id']==runid];valid=[q for q in rr if not q['parse_error_present']]
  details.append({'run_id':runid,'date':x['config']['date'],'model':x['config']['agent_args']['model_name'],'population':45,'successes':len(passes),'published_score':len(passes)/45,'parse_error_tasks':sum(q['parse_error_present'] for q in rr),'no_parse_error_tasks':len(valid),'no_parse_error_successes':sum(q['native_score'] for q in valid),'no_parse_error_mean':sum(q['native_score'] for q in valid)/len(valid) if valid else None,'logged_exception_tasks':sum(q['logged_exception_present'] for q in rr),'mapped_calls':len(logs),'exception_types':dict(collections.Counter(k for q in rr for k in q['recorded_exception_types']))})
  sources.append({'filename':r['path'],'url':url,'bytes':r['size'],'sha256':r['lfs']['oid'],'evaluator_url':eurl,'evaluator_sha256':EVAL_SHA})
 assert all(u==universes[0] for u in universes)
 ledger=ROOT/'hal_mixed_ledger.jsonl';ledger.write_text(''.join(json.dumps(q,sort_keys=True,allow_nan=False)+'\n' for q in rows))
 ck=check(ledger,['run_id','task_id']);assert ck['valid'] and ck['rows']==135
 reports={name:summarize(ledger,['run_id'],rules,'error') for name,rules in [('published',[]),('no_recorded_parse_error',[('parse_error_present',False)]),('no_recorded_call_exception',[('logged_exception_present',False)])]}
 for g in reports['no_recorded_parse_error']['groups']:
  d=next(d for d in details if d['run_id']==g['group'][0]['value']);assert g['population_count']==d['no_parse_error_tasks'] and math.isclose(g['policy_score_mean'],d['no_parse_error_mean'],abs_tol=1e-12)
 write('ledger_check.json',ck);write('reporter_results.json',reports);write('verification.json',{'all_selected_reported':True,'rows':135,'shared_task_ids':45,'same_universe':True,'missing_grades':0,'new_inference':0,'runs':details,'limitations':['Historical archives; current leaderboard/paper membership not established','No recorded parse error means only evaluator field absence under pinned evaluator; not proof of successful scientific reproduction','No exception in archived calls is narrower than complete execution success','Selection by size limits generalization; conditional means do not correct end-to-end grades']})
 write('source_manifest.json',{'dataset_revision':plan['dataset_revision'],'dataset_license':'unknown; raw redistribution excluded','selection_plan_sha256':sha(ROOT/'selection_plan.json'),'sources':sources,'official_decryption_sources':[{'url':'https://raw.githubusercontent.com/princeton-pli/hal-harness/'+DECRYPT_COMMIT+'/hal/utils/'+n,'sha256':h} for n,h in DECRYPT_HASHES.items()],'canonical_reporter_sha256':{n:sha(ROOT/n) for n in ['summarize_ledger.py','check_ledger.py']}})
 print(json.dumps(details,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--cache-dir',type=Path);a=p.parse_args()
 if a.cache_dir:
  assert ROOT!=a.cache_dir.resolve() and ROOT not in a.cache_dir.resolve().parents;run(a.cache_dir)
 else:
  with tempfile.TemporaryDirectory(prefix='aes_hal_mixed_raw_') as t:run(Path(t))
