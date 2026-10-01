"""Audit WildClawBench's released table and one independently scored model.

Requires pyarrow. Uses only downloaded data; no inference API calls.
Run with a Python environment containing pyarrow: python independent_audit.py
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import tarfile

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'independent_data' / 'wildclaw'
rows = pq.read_table(DATA / 'train.parquet').to_pylist()
assert len(rows) == 720
assert len({(r['model_name'], r['task_id']) for r in rows}) == 720
models = sorted({r['model_name'] for r in rows})
task_sets = [{r['task_id'] for r in rows if r['model_name'] == model} for model in models]
assert len(models) == 12 and all(len(tasks) == 60 for tasks in task_sets)
assert all(tasks == task_sets[0] for tasks in task_sets)

trace_summary = {}
for model in models:
    selected = [r for r in rows if r['model_name'] == model]
    roles = Counter(json.loads(r['trajectory'])[-1]['role'] for r in selected)
    trace_summary[model] = dict(roles)

# Preselected by smallest TAR raw-output archive, before reading outcomes.
selected_model = 'Claude Fable 5'
selected = [r for r in rows if r['model_name'] == selected_model]
scores = {}
archive = DATA / 'output_claude_fable5.tar.gz'
with tarfile.open(archive) as handle:
    for member in handle.getmembers():
        if member.isfile() and member.name.endswith('/score.json'):
            task_id = member.name.split('/')[2]
            assert task_id not in scores
            scores[task_id] = json.load(handle.extractfile(member))['overall_score']
    published = json.load(handle.extractfile('output_claude_fable5/summary_all_new-api_claude-fable-5.json'))
headers = {}
for path in sorted((DATA / 'sessions' / 'claude_fable5').glob('*.jsonl')):
    with path.open() as handle:
        header = json.loads(handle.readline())
    assert header['task_id'] not in headers
    headers[header['task_id']] = header
assert set(scores) == set(headers) == {r['task_id'] for r in selected}
run_data = []
for row in selected:
    messages = json.loads(row['trajectory'])
    task_id = row['task_id']
    score = scores[task_id]
    assert isinstance(score, (int, float)) and 0 <= score <= 1
    run_data.append({
        'task_id': task_id,
        'model': selected_model,
        'task_category': row['task_category'],
        'last_role': messages[-1]['role'],
        'stop_reason': messages[-1].get('stopReason'),
        'trace_status': headers[task_id]['trace_status'],
        'score': score,
    })

def mean(items):
    return sum(r['score'] for r in items) / len(items)

all_mean = mean(run_data)
assert abs(all_mean - published['global_avg']) < 1e-8
assistant = [r for r in run_data if r['last_role'] == 'assistant']
clean = [r for r in run_data if r['trace_status'] == 'completed']
result = {
    'dataset': 'internlm/WildClawBench-Trajectories',
    'row_count': len(rows),
    'models': len(models),
    'shared_tasks': len(task_sets[0]),
    'last_role_by_model': trace_summary,
    'nonassistant_ending_total': sum(sum(v for k, v in d.items() if k != 'assistant') for d in trace_summary.values()),
    'selected_model': selected_model,
    'selection_reason': 'Size-guided TAR archive convenience selection before task scores; smaller ZIP archives omitted',
    'selected_model_summary': {
        'all_runs': len(run_data), 'all_mean_score': all_mean,
        'assistant_ending_runs': len(assistant), 'assistant_ending_mean_score': mean(assistant),
        'clean_execution_runs': len(clean), 'clean_execution_mean_score': mean(clean),
        'status_counts': dict(Counter(r['trace_status'] for r in run_data)),
        'last_role_status_counts': dict(Counter(r['last_role'] + '/' + r['trace_status'] for r in run_data)),
        'error_positive_scores': [r for r in run_data if r['trace_status'] == 'error' and r['score'] > 0],
    },
    'runs': run_data,
    'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (DATA / 'train.parquet', archive)},
}
(ROOT / 'independent_results.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
ledger = ROOT / 'run_accounting'
ledger.mkdir(exist_ok=True)
selected_by_task = {r['task_id']: r for r in run_data}
with (ledger / 'wildclaw_released_pairs.jsonl').open('w') as handle:
    for row in rows:
        scored = selected_by_task.get(row['task_id']) if row['model_name'] == selected_model else None
        entry = {
            'model': row['model_name'], 'task_id': row['task_id'],
            'retention': 'released',
            'last_original_role': json.loads(row['trajectory'])[-1]['role'],
            'execution_status': scored['trace_status'] if scored else None,
            'score_available': True if scored else None,
            'native_score': scored['score'] if scored else None,
            'score_scale': [0, 1], 'retry_of': None, 'failure_attribution': None,
            'source_revision': 'd2816016a7a7b41fa6b7ba368b28ddafcb54fd93',
        }
        handle.write(json.dumps(entry, sort_keys=True) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('runs', 'last_role_by_model')}, indent=2))
