"""Use unmodified bounds on naturally unavailable recorded grades in the search grid."""
import json
from pathlib import Path
from bounded_comparison import report_selected
ROOT=Path(__file__).resolve().parent


def demonstrate(root):
    attempts={}
    for line in (root/'run_accounting/cmu_attempts.jsonl').read_text().splitlines():
        r=json.loads(line)
        if r['attempt_id'] in attempts: raise ValueError('Duplicate attempt')
        attempts[r['attempt_id']]=r
    slots=[json.loads(line) for line in (root/'run_accounting/cmu_search_slots.jsonl').read_text().splitlines()]
    models=sorted({s['model'] for s in slots}); tasks_by_model={m:set() for m in models}
    rows=[]; unknown=[]
    for slot in slots:
        # Unit is a scheduled pass, not a fabricated released attempt identity.
        task=json.dumps([slot['domain'],slot['task_id'],slot['pass']],separators=(',',':'))
        if task in tasks_by_model[slot['model']]:raise ValueError('Duplicate scheduled slot')
        tasks_by_model[slot['model']].add(task)
        if slot['observed_attempt_id'] is None:
            unknown.append(slot);continue
        attempt=attempts[slot['observed_attempt_id']]
        rows.append({'model':slot['model'],'task_id':task,'score_available':attempt['score_available'],'native_score':attempt['native_score'],'score_scale':attempt['score_scale']})
    tasks=sorted(tasks_by_model[models[0]])
    if any(t!=set(tasks) for t in tasks_by_model.values()):raise ValueError('Unequal scheduled rosters')
    report=report_selected(rows,tasks,models)
    return {'interpretation':'Actual unavailable recorded grade, not artificial masking. Preserves all released search grades including excluded-run grades. Bounds concern recorded-grade summaries, not achievement or a new all-attempt failure policy. The absent scheduled slot has no fabricated attempt ID.','scheduled_passes_per_model':len(tasks),'known_records':len(rows),'unavailable_slots':unknown,'report':report,'certified_pairs':sum(p['certified_order'] is not None for p in report['pairs'])}

if __name__=='__main__':
    result=demonstrate(ROOT)
    (ROOT/'cmu_bounded_reporting_example.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ['scheduled_passes_per_model','known_records','unavailable_slots','certified_pairs']},indent=2))
    print(json.dumps(result['report']['models'],indent=2))
