"""Audit final-role and native stopReason metadata in all 720 released pairs.

No inference or network calls. Requires pyarrow; run with Python 3.
This script only writes terminal_measurement_results.json.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'independent_data/wildclaw/train.parquet'
rows = pq.read_table(SOURCE).to_pylist()
assert len(rows) == 720
assert len({(r['model_name'], r['task_id']) for r in rows}) == 720
models = sorted({r['model_name'] for r in rows})
tasks = [{r['task_id'] for r in rows if r['model_name'] == m} for m in models]
assert len(models) == 12 and all(len(t) == 60 and t == tasks[0] for t in tasks)


def reason_state(event):
    if 'stopReason' not in event:
        return 'absent'
    if event['stopReason'] is None:
        return 'null'
    assert isinstance(event['stopReason'], str)
    return 'present'


records = []
all_event_availability = Counter()
for row in sorted(rows, key=lambda r: (r['model_name'], r['task_id'])):
    messages = json.loads(row['trajectory'])
    assert messages
    for event in messages:
        all_event_availability[(event['role'], reason_state(event))] += 1
    terminal = messages[-1]
    records.append({
        'model': row['model_name'],
        'task_id': row['task_id'],
        'task_category': row['task_category'],
        'terminal_role': terminal['role'],
        'stop_reason_availability': reason_state(terminal),
        'native_stop_reason': terminal.get('stopReason'),
    })


def summarize(selected):
    matrix = Counter((r['terminal_role'], r['stop_reason_availability'],
                      r['native_stop_reason']) for r in selected)
    assistant = sum(r['terminal_role'] == 'assistant' for r in selected)
    stop = sum(r['native_stop_reason'] == 'stop' for r in selected)
    disagreement = sum((r['terminal_role'] == 'assistant') !=
                       (r['native_stop_reason'] == 'stop') for r in selected)
    return {
        'released_pairs': len(selected),
        'assistant_ending_count': assistant,
        'terminal_native_stop_count': stop,
        'assistant_ending_fraction': assistant / len(selected),
        'terminal_native_stop_fraction': stop / len(selected),
        'predicate_disagreement_count': disagreement,
        'predicate_disagreement_fraction': disagreement / len(selected),
        'assistant_ending_non_stop_count': sum(
            r['terminal_role'] == 'assistant' and r['native_stop_reason'] != 'stop'
            for r in selected),
        'role_reason_matrix': [
            {'terminal_role': role, 'stop_reason_availability': state,
             'native_stop_reason': reason, 'count': count}
            for (role, state, reason), count in sorted(
                matrix.items(), key=lambda item: tuple(str(v) for v in item[0]))
        ],
    }


result = {
    'dataset': 'internlm/WildClawBench-Trajectories',
    'source_revision': 'd2816016a7a7b41fa6b7ba368b28ddafcb54fd93',
    'source_path': str(SOURCE.relative_to(ROOT)),
    'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'measurement_definitions': {
        'assistant_ending': "last original message role equals 'assistant'",
        'terminal_native_stop': "last original message stopReason equals 'stop'",
        'availability': 'Absent key, explicit null, and present string are counted separately.',
        'scope': 'Released pairs only; native labels are reported without inferring execution completion, task success, or cause.',
    },
    'model_count': len(models),
    'shared_task_count': len(tasks[0]),
    'overall': summarize(records),
    'by_model': {m: summarize([r for r in records if r['model'] == m]) for m in models},
    'all_original_event_stop_reason_availability': [
        {'role': role, 'stop_reason_availability': state, 'event_count': count}
        for (role, state), count in sorted(all_event_availability.items())
    ],
    'runs': records,
}
assert result['overall']['released_pairs'] == sum(
    m['released_pairs'] for m in result['by_model'].values())
assert sum(r['count'] for r in result['overall']['role_reason_matrix']) == 720
output = ROOT / 'terminal_measurement_results.json'
output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'runs'}, indent=2))
