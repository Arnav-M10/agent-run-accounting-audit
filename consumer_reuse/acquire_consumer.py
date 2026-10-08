"""Fetch pinned public consumer; retain only derived grade/identity metadata privately."""
import argparse,hashlib,json,subprocess
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 manifest=json.loads((Path(__file__).parent/'source_manifest.json').read_text())
 partial=a.output.with_suffix(a.output.suffix+'.partial');digest=hashlib.sha256();size=rows=0
 proc=subprocess.Popen(['curl','--fail','--location','--silent','--show-error','--max-time','180',manifest['consumer_data_url']],stdout=subprocess.PIPE)
 try:
  with partial.open('w') as out:
   for line in proc.stdout:
    digest.update(line);size+=len(line)
    if not line.strip():continue
    r=json.loads(line)
    if r.get('agent_scaffold')!='general-agentbench':continue
    keep={k:r[k] for k in ['agent_scaffold','benchmark','record_type']}
    if r['record_type']=='trial_result':
     keep.update({k:r[k] for k in ['task_id','agent_model','trial','result']});keep['metadata']={'source_reward':r['metadata']['source_reward']}
    out.write(json.dumps(keep,sort_keys=True,allow_nan=False)+'\n');rows+=1
  if proc.wait()!=0:raise ValueError('Source download failed')
  if size!=manifest['consumer_full_bytes'] or digest.hexdigest()!=manifest['consumer_full_sha256']:raise ValueError('Pinned source size/hash mismatch')
  partial.replace(a.output)
  data={'source_url':manifest['consumer_data_url'],'source_sha256':digest.hexdigest(),'source_bytes':size,'retained_metadata_rows':rows,'derived_metadata_sha256':hashlib.sha256(a.output.read_bytes()).hexdigest()}
  a.output.with_suffix(a.output.suffix+'.source.json').write_text(json.dumps(data,indent=2)+'\n')
  print(json.dumps(data,indent=2))
 finally:
  if proc.poll() is None:proc.kill();proc.wait()
if __name__=='__main__':main()
