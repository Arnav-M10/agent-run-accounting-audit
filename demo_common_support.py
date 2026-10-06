"""Regenerate all three support diagnostics; status coverage is explicit."""
import json
from pathlib import Path
from common_support_audit import compare
root=Path(__file__).resolve().parent
rows=[json.loads(s) for s in (root/'run_accounting/wildclaw_released_pairs.jsonl').read_text().splitlines()]
result={}
for field,value in [('last_original_role','assistant'),('native_stop_reason','stop'),('execution_status','completed')]:
    available={r['model'] for r in rows if r.get('execution_status') is not None}
    subset=rows if field!='execution_status' else [r for r in rows if r['model'] in available]
    result[field]=compare(subset,field,value)
    result[field]['source_coverage']={'released_models':12,'analyzed_models':result[field]['models'],
        'restriction':'fully exporter-status-covered models' if field=='execution_status' else 'all released models'}
    result[field]['common_reversal_count']=sum(p['common_reversal'] is True for p in result[field]['pairs'])
    reversed_pairs=[p for p in result[field]['pairs'] if p['separate_reversal'] is True]
    result[field]['separate_reversal_absolute_margins']={f:{
        'minimum':min((abs(p[f]) for p in reversed_pairs),default=None),
        'maximum':max((abs(p[f]) for p in reversed_pairs),default=None)}
        for f in ['full_gap','separate_gap']}
(root/'common_support_results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
for k,v in result.items():print(k,v['classification_counts'],'all common reversals',v['common_reversal_count'])
