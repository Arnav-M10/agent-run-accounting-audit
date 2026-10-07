"""Exploratory leave-one-category-out reference sensitivity, added after main results."""
import json
from pathlib import Path
from mask_reference_audit import audit
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    rows=[json.loads(x) for x in (ROOT/'run_accounting/wildclaw_released_pairs.jsonl').read_text().splitlines()]
    result={'interpretation':'Outcome-informed exploratory sensitivity; each omitted category changes the target task population. No confirmatory inference.','omissions':{}}
    for category in sorted({r['task_id'].split('_',1)[0] for r in rows}):
        reduced=[r for r in rows if r['task_id'].split('_',1)[0]!=category]
        report=audit(reduced)
        result['omissions'][category]={rule: {'task_count':r['task_count'],'gap_displacement':r['metrics']['mean_absolute_common_gap_displacement_points']} for rule,r in report['rules'].items()}
    (ROOT/'mask_reference_sensitivity.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
