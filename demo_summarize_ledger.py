"""Read-only demonstration and comparison with the existing full-roster summary."""
import json
import math
from pathlib import Path
from summarize_ledger import summarize


def demonstrate(root):
    expected = json.loads((root / 'full_roster_results.json').read_text())['models']
    policies = {
        'all': ([], 'native_mean'),
        'assistant': ([('last_original_role', 'assistant')], 'assistant_mean'),
        'native_stop': ([('native_stop_reason', 'stop')], 'native_stop_mean'),
        'exporter_completed': ([('execution_status', 'completed')], 'export_completed_mean'),
    }
    output = {}
    comparisons = 0
    for name, (rules, metric) in policies.items():
        report = summarize(root / 'run_accounting/wildclaw_released_pairs.jsonl', ['model'], rules, 'error')
        for group in report['groups']:
            model = group['group'][0]['value']
            if metric not in expected[model]:
                assert name == 'exporter_completed' and expected[model]['export_status_examined_runs'] == 0
                assert group['population_count'] == 0 and group['policy_score_mean'] is None
                continue
            reference = expected[model][metric]
            actual = group['policy_score_mean']
            assert actual is None if reference is None else math.isclose(actual, reference, rel_tol=0, abs_tol=1e-12), (model, name)
            comparisons += 1
        report['ledger'] = 'run_accounting/wildclaw_released_pairs.jsonl'
        output[name] = report
    output['verification'] = {'matched_model_policy_means': comparisons,
        'exporter_status_unexamined_models': ['Qwen3.8 Max', 'Qwen3.8-27B (vLLM)']}
    return output


if __name__ == '__main__':
    print(json.dumps(demonstrate(Path(__file__).resolve().parent), indent=2, allow_nan=False))
