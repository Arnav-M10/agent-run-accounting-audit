"""Exploratory alternative grade-derived difficulty blocking, added after main results."""
import json
from pathlib import Path
from mask_reference_audit import audit
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    rows=[json.loads(x) for x in (ROOT/'run_accounting/wildclaw_released_pairs.jsonl').read_text().splitlines()]
    result=audit(rows,block_by='category_difficulty')
    (ROOT/'mask_reference_block_sensitivity.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v['metrics'] for k,v in result['rules'].items()},indent=2))
