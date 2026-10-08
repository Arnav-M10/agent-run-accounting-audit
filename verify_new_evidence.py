"""Verify packaged disclosure results and optional pinned private source caches.
No inference. No downloads. Outputs are written only into a temporary directory.
"""
import argparse, hashlib, json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def run(args):
 return subprocess.check_output([sys.executable,*map(str,args)],cwd=ROOT,text=True)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--consumer-metadata',type=Path,help='Private output of consumer_reuse/acquire_consumer.py')
 p.add_argument('--session-shards',type=Path,help='Private pinned v2 Parquet shard directory; PyArrow required')
 a=p.parse_args();checks={}
 actual=json.loads(run(['winner_recovery.py','run_accounting/wildclaw_released_pairs.jsonl']))
 if actual!=json.loads((ROOT/'winner_recovery_results.json').read_text()):raise ValueError('Packaged recovery result differs')
 run(['verify_winner_recovery.py']);checks['recovery']='Packaged ledger replay, exhaustive fixtures and tolerance regression passed; not raw extraction validation.'
 with tempfile.TemporaryDirectory(prefix='aes_evidence_check_') as tmp:
  if a.consumer_metadata:
   cache=a.consumer_metadata.resolve()
   expected=json.loads((ROOT/'consumer_reuse/acquisition_check.json').read_text())
   if hashlib.sha256(cache.read_bytes()).hexdigest()!=expected['derived_metadata_sha256']:raise ValueError('Consumer metadata cache hash mismatch')
   run(['consumer_reuse/check_consumer.py','--consumer',cache,'--ledger','run_accounting/cmu_attempts.jsonl','--out',tmp])
   for name in ['consumer_check.json','reduction_replay.csv']:
    if (Path(tmp)/name).read_bytes()!=(ROOT/'consumer_reuse'/name).read_bytes():raise ValueError('Consumer replay differs: '+name)
   checks['consumer']='Pinned private derived cache matches all grade groups and reductions; full-source acquisition checksum recorded separately.'
  if a.session_shards:
   lines=run(['session_score_check/replay.py','--root',a.session_shards.resolve()]).splitlines()
   actual=[json.loads(x) for x in lines if x.strip()]
   expected=json.loads((ROOT/'session_score_check/results.json').read_text())
   if len(actual)!=len(expected):raise ValueError('Session run count differs')
   for row,saved in zip(actual,expected):
    if any(saved.get(key)!=value for key,value in row.items()):raise ValueError('Session grade/status replay differs')
   checks['sessions']='All nine source shard hashes and three within-run score populations verified; historical generating join remains unknown.'
 print(json.dumps(checks,indent=2))
if __name__=='__main__':main()
