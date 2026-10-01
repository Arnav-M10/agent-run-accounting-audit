"""Enumerate descriptive model-pair ordering changes across all released models."""
from pathlib import Path
from itertools import combinations
import json
root=Path(__file__).resolve().parent
models=json.loads((root/'full_roster_results.json').read_text())['models']
result={'interpretation':'Fixed released-score comparisons under different hypothetical inclusion rules; no inference of general model superiority or correction to published scoring.','policies':{}}
for rule in ['assistant_mean','native_stop_mean','export_completed_mean']:
    available=[m for m,d in models.items() if rule in d]
    pairs=list(combinations(available,2));changes=[];ties=[]
    for a,b in pairs:
        native=models[a]['native_mean']-models[b]['native_mean']
        conditional=models[a][rule]-models[b][rule]
        if native*conditional<0:changes.append([a,b])
        if native==0 or conditional==0:ties.append([a,b])
    result['policies'][rule]={'models':len(available),'pairs':len(pairs),'reversed_pairs':len(changes),'reversal_pairs':changes,'ties':ties}
(root/'policy_order_results.json').write_text(json.dumps(result,indent=2)+'\n')
print({k:(v['reversed_pairs'],v['pairs']) for k,v in result['policies'].items()})
