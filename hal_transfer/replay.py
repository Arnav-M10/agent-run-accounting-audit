#!/usr/bin/env python3
"""Replay packaged HAL metadata offline, without cryptography or acquisition."""
import argparse, hashlib, json
from pathlib import Path
from check_ledger import check
from summarize_ledger import summarize
ROOT=Path(__file__).resolve().parent

def portable(x):
    if isinstance(x, dict):return {k:portable(v) for k,v in x.items()}
    if isinstance(x, list):return [portable(v) for v in x]
    if isinstance(x, str) and x.startswith(str(ROOT)+'/'):return x[len(str(ROOT))+1:]
    return x

def replay(verify_only=False):
    manifest=json.loads((ROOT/'source_manifest.json').read_text())
    for name,digest in manifest['canonical_reporters'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Reporter differs from declared source: '+name)
    ledger=ROOT/'hal_task_ledger.jsonl'
    checked=portable(check(ledger,['run_id','task_id']))
    if not checked['valid'] or checked['rows']!=90:raise ValueError('Invalid packaged HAL ledger')
    reports=portable({'published_end_to_end':summarize(ledger,['run_id'],[],'error'),
        'explicit_no_parse_error':summarize(ledger,['run_id'],[('parse_error_present',False)],'error'),
        'explicit_no_call_exception':summarize(ledger,['run_id'],[('logged_exception_present',False)],'error')})
    for mode in ['explicit_no_parse_error','explicit_no_call_exception']:
        groups=reports[mode]['groups']
        for g in groups:
            if g['population_count'] or g['policy_score_mean'] is not None:raise ValueError('Expected empty certified support')
            known='generalist' in g['group'][0]['value']
            if (g['known_ineligible_count'],g['unknown_eligibility_count'])!=((45,0) if known else (0,45)):
                raise ValueError('Eligibility evidence not distinguished')
    for name,value in [('ledger_check.json',checked),('reporter_results.json',reports)]:
        if verify_only:
            if json.loads((ROOT/name).read_text())!=value:raise ValueError('Saved report mismatch: '+name)
        else:(ROOT/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print('Offline HAL replay:90 records; known-error and unknown eligibility distinct; empty means null.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify-only',action='store_true');a=p.parse_args();replay(a.verify_only)
