#!/usr/bin/env python3
"""Offline reporting of source-pinned public HAL metadata; never runs an agent."""
import argparse, base64, collections, hashlib, json, math, subprocess, tempfile, zipfile
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from check_ledger import check
from summarize_ledger import summarize

ROOT=Path(__file__).resolve().parent
REV='e7dcedc82b4f4bc819a170fd6616bdb44841c71e'
BASE='https://huggingface.co/datasets/agent-evals/hal_traces/resolve/'+REV+'/'
SOURCES=[
 {'kind':'operational_error','filename':'corebench_hard_hal_generalist_agent_1747200995_UPLOAD.zip','bytes':945255,'sha256':'89894a8e9347878ab2c039b61b9518a7599a10bf9d790f7727fa084a491c9816'},
 {'kind':'control','filename':'corebench_hard_claude_code_claudeopus41_1764560915_UPLOAD.zip','bytes':2672,'sha256':'f0876164e46dc23df62c87008068bda2c3a57297f133ef382f26fae788f66b33'}]
CODE_COMMIT='db2a824aa6a07ce8f1097258327fdfb7dd04c2ac'
EVAL_URL='https://raw.githubusercontent.com/princeton-pli/hal-harness/'+CODE_COMMIT+'/hal/benchmarks/corebench.py'
EVAL_SHA='7d04be1e8fa92a6db0c535e490708dbb7a3605ff88ff05ea5d19e3ee4fa0090f'
DECRYPT_COMMIT='16bb03ebc11577fb5ea6dc8bb6c968387085e6aa'
DECRYPT_BASE='https://raw.githubusercontent.com/princeton-pli/hal-harness/'+DECRYPT_COMMIT+'/hal/utils/'
DECRYPT_SOURCES=[('decrypt.py','0406a8c44b466d390e69a72fd585c0e905babbae5e4150dcf71357287f2afcfc'),('json_encryption.py','8aa91ca6ddb67005d276159a280e566cd3e3a2327247bb96136c0de0ab4ac895')]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def obtain(cache,name,url,expected,size=None):
 p=cache/name
 if not p.exists():subprocess.run(['curl','--fail','--location','--max-time','60','--silent','--show-error',url,'-o',str(p)],check=True)
 if sha(p)!=expected or size is not None and p.stat().st_size!=size:raise ValueError('Source verification failed: '+name)
 return p

def decode(path):
 # Exact algorithm and intentionally published password from official decrypt.py.
 with zipfile.ZipFile(path) as z:
  if len(z.namelist())!=1:raise ValueError('Expected one encrypted result')
  e=json.loads(z.read(z.namelist()[0]))
 key=PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,salt=base64.b64decode(e['salt']),iterations=480000).derive(b'hal1234')
 return json.loads(Fernet(base64.urlsafe_b64encode(key)).decrypt(base64.b64decode(e['encrypted_data'])))

def portable(x):
 if isinstance(x,dict):return {k:portable(v) for k,v in x.items()}
 if isinstance(x,list):return [portable(v) for v in x]
 if isinstance(x,str) and x.startswith(str(ROOT)+'/'):return x[len(str(ROOT))+1:]
 return x
def write(name,x): (ROOT/name).write_text(json.dumps(portable(x),indent=2,allow_nan=False)+'\n')

def run(cache):
 cache.mkdir(parents=True,exist_ok=True)
 evaluator=obtain(cache,'corebench_atrun.py',EVAL_URL,EVAL_SHA)
 for name,digest in DECRYPT_SOURCES:obtain(cache,'official_'+name,DECRYPT_BASE+name,digest)
 # Preserve source code pin; metadata interpretation is documented, not regrading.
 assert '"error": str(e)' in evaluator.read_text()
 rows=[];run_info=[];universes=[]
 for src in SOURCES:
  p=obtain(cache,src['filename'],BASE+src['filename'],src['sha256'],src['bytes']);x=decode(p);cfg=x['config'];r=x['results']
  passes=r['successful_tasks'];fails=r['failed_tasks']
  assert len(passes)==len(set(passes)) and len(fails)==len(set(fails))
  assert not set(passes)&set(fails)
  ids=set(passes)|set(fails);assert len(ids)==45;universes.append(ids)
  assert math.isclose(r['accuracy'],len(passes)/45,rel_tol=0,abs_tol=1e-12)
  ex=collections.defaultdict(list)
  if src['kind']=='operational_error':
   assert cfg['run_id']=='corebench_hard_hal_generalist_agent_1747200995'
   assert x['git_info']['commit']==CODE_COMMIT
   assert set(x['raw_eval_results'])==ids
   for record in x['raw_logging_results']:
    task=record.get('weave_task_id') or record.get('attributes',{}).get('weave_task_id')
    assert task in ids
    if record.get('exception'):
     error=record['exception'];error=json.loads(error) if isinstance(error,str) else error
     ex[task].append(error)
   assert set(ex)==ids and all(len(v)==1 for v in ex.values())
  for task in sorted(ids):
   score=int(task in set(passes))
   row={'run_id':cfg['run_id'],'task_id':task,'benchmark':'corebench_hard','native_score':score,'score_scale':[0,1],'score_available':True,'source_outcome':'success' if score else 'failure','source_archive_sha256':src['sha256'],'source_grade_policy':('all_task_questions_correct; parse_error assigns zero (recorded evaluator commit)' if src['kind']=='operational_error' else 'archived successful_tasks/failed_tasks labels; no raw grading records'),'execution_status':None,'logged_exception_present':None,'parse_error_present':None,'recorded_exception_type':None,'operational_failure_kind':None,'status_coverage':'not_exposed_in_processed_archive'}
   if src['kind']=='operational_error':
    ev=x['raw_eval_results'][task];err=ex[task][0]
    assert ev['error']=='Expecting value: line 1 column 1 (char 0)'
    assert ev['correct_written_answers']==ev['correct_vision_answers']==score==0
    assert ev['total_written_questions']+ev['total_vision_questions']>0
    if err['type']=='BadRequestError':
     assert 'Your credit balance is too low' in err['message'];kind='provider_credit_unavailable'
    elif err['type']=='APIConnectionError':
     assert 'can only concatenate str' in err['message'];kind='client_message_type_error'
    else:raise ValueError('Unexpected exception kind')
    row.update(execution_status='recorded_call_exception',logged_exception_present=True,parse_error_present=True,recorded_exception_type=err['type'],operational_failure_kind=kind,status_coverage='direct_task_join')
   rows.append(row)
  run_info.append({'run_id':cfg['run_id'],'agent_name':cfg['agent_name'],'date':cfg['date'],'rows':45,'successes':len(passes),'failures':len(fails),'source_accuracy':r['accuracy'],'status_coverage':'direct_task_join' if ex else 'not_exposed_in_processed_archive'})
 assert universes[0]==universes[1]
 ledger=ROOT/'hal_task_ledger.jsonl';ledger.write_text(''.join(json.dumps(r,sort_keys=True,allow_nan=False)+'\n' for r in rows))
 validated=check(ledger,['run_id','task_id']);assert validated['valid'] and validated['rows']==validated['numeric_scores']==90
 reports={'published_end_to_end':summarize(ledger,['run_id'],[],'error'),'explicit_no_parse_error':summarize(ledger,['run_id'],[('parse_error_present',False)],'error'),'explicit_no_call_exception':summarize(ledger,['run_id'],[('logged_exception_present',False)],'error')}
 for mode in ['explicit_no_parse_error','explicit_no_call_exception']:
  for g in reports[mode]['groups']:
   assert g['population_count']==0 and g['excluded_count']==45 and g['policy_score_mean'] is None
   assert g['unknown_score_count']==0
 for g in reports['published_end_to_end']['groups']:
  assert g['population_count']==g['scored_count']==45
  expected=0 if 'generalist' in g['group'][0]['value'] else 19/45
  assert math.isclose(g['policy_score_mean'],expected,abs_tol=1e-12)
 write('ledger_check.json',validated);write('reporter_results.json',reports)
 summary={'population_rows':90,'unique_tasks':45,'common_task_ids':45,'identical_task_universe':True,'all_scores_available':True,'published_generalist_accuracy':0,'published_control_accuracy':19/45,'directly_observed_exception_tasks':45,'directly_observed_parse_error_tasks':45,'exception_types':dict(collections.Counter(r['recorded_exception_type'] for r in rows if r['recorded_exception_type'])),'operational_failure_kinds':dict(collections.Counter(r['operational_failure_kind'] for r in rows if r['operational_failure_kind'])),'control_unknown_status_tasks':45,'no_parse_error_known_support_generalist':0,'no_parse_error_known_support_control':0,'no_parse_error_control_support_reason':'status unknown; explicit false rule cannot certify error absence','missing_grades':0,'new_inference_calls':0,'new_human_participants':0,'source_grade_semantics':'Known end-to-end zero on parse error; not missing grades','runs':run_info}
 write('verification.json',summary)
 write('source_manifest.json',{'dataset_revision':REV,'dataset_license':'unknown; no card/license metadata in inspected official repository','redistribution':'raw archives/traces excluded; adapter and derived metadata only','sources':[{**s,'url':BASE+s['filename']} for s in SOURCES],'evaluator':{'url':EVAL_URL,'sha256':EVAL_SHA,'recorded_run_commit':CODE_COMMIT},'official_decryption_sources':[{'url':DECRYPT_BASE+n,'sha256':h} for n,h in DECRYPT_SOURCES],'canonical_reporters':{n:sha(ROOT/n) for n in ['check_ledger.py','summarize_ledger.py']}})
 print(json.dumps(summary,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache-dir',type=Path,help='Private raw-download cache outside release directory');a=p.parse_args()
 if a.cache_dir:
  if ROOT==a.cache_dir.resolve() or ROOT in a.cache_dir.resolve().parents:raise ValueError('Keep raw cache outside release directory')
  run(a.cache_dir)
 else:
  with tempfile.TemporaryDirectory(prefix='aes_hal_raw_') as t:run(Path(t))
