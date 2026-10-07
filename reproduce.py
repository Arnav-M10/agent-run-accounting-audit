"""Run all local audits after acquiring the pinned inputs; no inference calls."""
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
for script in ('audit.py','independent_audit.py','extension_audit.py','zip_score_audit.py','terminal_measurement_audit.py','full_roster_audit.py','policy_order_audit.py','demo_common_support.py','coherence_audit.py','verify_accounting.py'):
    subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,check=True)
import json
reports={}
for name,identity,reference in [('cmu_attempts.jsonl','attempt_id',False),('cmu_search_slots.jsonl','benchmark,domain,model,task_id,pass',True),('wildclaw_released_pairs.jsonl','model,task_id',False)]:
    args=[sys.executable,str(ROOT/'check_ledger.py'),str(Path('run_accounting')/name),'--identity',identity]
    if reference:args+=['--reference-ledger','run_accounting/cmu_attempts.jsonl']
    reports[name]=json.loads(subprocess.check_output(args,text=True,cwd=ROOT))
(ROOT/'ledger_check_results.json').write_text(json.dumps(reports,indent=2)+'\n')
print('All audits, reusable ledger checks, completed.')

from demo_summarize_ledger import demonstrate
(ROOT/'summarize_ledger_example.json').write_text(json.dumps(demonstrate(ROOT),indent=2,allow_nan=False)+'\n')
print('Reusable reporting command matched 46 model-policy means.')

from demo_cmu_reporting import demonstrate as demonstrate_cmu
(ROOT/'cmu_reporting_example.json').write_text(json.dumps(demonstrate_cmu(ROOT),indent=2,allow_nan=False)+'\n')
print('Unchanged reporter matched 12 CMU benchmark-population means; mixed native scales rejected.')
