"""Enumerate fixed-grade ordering cycles caused by pair-specific task support."""
import argparse
import json
import math
from itertools import combinations
from pathlib import Path
from common_support_audit import compare, EPS
from summarize_ledger import equal


def directed_cycle(graph):
    """Return one closed directed path, or None, including cycles longer than three."""
    state, stack, position = {}, [], {}
    def visit(node):
        state[node] = 1
        position[node] = len(stack)
        stack.append(node)
        for target in sorted(graph[node]):
            if state.get(target, 0) == 1:
                return stack[position[target]:] + [target]
            if state.get(target, 0) == 0:
                result = visit(target)
                if result is not None: return result
        stack.pop()
        position.pop(node)
        state[node] = 2
        return None
    for node in sorted(graph):
        if state.get(node, 0) == 0:
            result = visit(node)
            if result is not None: return result
    return None


def audit(rows, field, value):
    support = compare(rows, field, value)  # validates identities, rosters and grades
    pairs = {(p['model_a'], p['model_b']): p for p in support['pairs']}
    models = sorted({r['model'] for r in rows})
    groups = {m: {r['task_id']: r for r in rows if r['model'] == m} for m in models}
    selected = {m: {t for t, r in g.items() if field in r and equal(r[field], value)}
                for m, g in groups.items()}
    global_tasks = set.intersection(*(selected[m] for m in models))

    def edge(a, b, kind):
        p = pairs[tuple(sorted((a, b)))]
        gap = p[kind]
        return None if gap is None else gap if a == p['model_a'] else -gap

    results = {}
    for kind in ('full_gap', 'separate_gap', 'common_gap'):
        cycles = []
        for triple in combinations(models, 3):
            a, b, c = triple
            gaps = [edge(a, b, kind), edge(b, c, kind), edge(c, a, kind)]
            if any(g is None for g in gaps):
                continue
            if all(g > EPS for g in gaps):
                order = [a, b, c]
            elif all(g < -EPS for g in gaps):
                order = [a, c, b]
            else:
                continue
            edges = []
            for winner, loser in zip(order, order[1:] + order[:1]):
                p = pairs[tuple(sorted((winner, loser)))]
                edges.append({'winner': winner, 'loser': loser,
                              'gap': edge(winner, loser, kind),
                              'common_count': p['common_count'],
                              'common_task_ids': p['common_task_ids']})
            cycles.append({'models': order, 'edges': edges,
                           'minimum_edge_gap': min(e['gap'] for e in edges)})
        values = [p[kind] for p in pairs.values()]
        width = support['score_scale'][1] - support['score_scale'][0]
        profile = []
        for f in (0, .005, .01, .02):
            threshold = f * width + EPS
            graph = {m: set() for m in models}
            for (a, b), pair in pairs.items():
                gap = pair[kind]
                if gap is None: continue
                if gap > threshold: graph[a].add(b)
                elif gap < -threshold: graph[b].add(a)
            witness = directed_cycle(graph)
            profile.append({'fraction_of_score_range': f, 'native_gap_threshold': f * width,
                            'cycle_count': sum(c['minimum_edge_gap'] > threshold for c in cycles),
                            'is_acyclic': witness is None, 'any_cycle_witness': witness})
        results[kind] = {'cycle_count': len(cycles), 'cycles': cycles,
                         'descriptive_margin_profile': profile,
                         'undefined_edges': sum(g is None for g in values),
                         'tied_edges': sum(g is not None and abs(g) <= EPS for g in values)}
    # These contrasts subtract one scalar per model and must be acyclic.
    assert results['full_gap']['cycle_count'] == 0
    assert results['separate_gap']['cycle_count'] == 0
    means = {m: math.fsum(groups[m][t]['native_score'] for t in sorted(global_tasks)) / len(global_tasks)
             for m in models} if global_tasks else None
    return {'predicate': support['predicate'], 'models': len(models),
            'tasks_per_model': support['tasks_per_model'],
            'triple_count': math.comb(len(models), 3), 'edge_tolerance': EPS,
            'orders': results, 'global_common_count': len(global_tasks),
            'global_common_task_ids': sorted(global_tasks), 'global_common_means': means,
            'interpretation': 'Strict observed cycles certify incompatibility with one scalar order. Pair-specific selected populations and fixed inherited grades; not judge inconsistency, statistical significance, or corrected ability.'}


def demonstrate(root):
    rows = [json.loads(s) for s in (root / 'run_accounting/wildclaw_released_pairs.jsonl').read_text().splitlines()]
    result = {}
    for field, value in [('last_original_role', 'assistant'), ('native_stop_reason', 'stop'), ('execution_status', 'completed')]:
        available = {r['model'] for r in rows if r.get('execution_status') is not None}
        subset = rows if field != 'execution_status' else [r for r in rows if r['model'] in available]
        result[field] = audit(subset, field, value)
        result[field]['restriction'] = 'ten status-covered models' if field == 'execution_status' else 'all twelve released models'
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('ledger', type=Path, nargs='?')
    p.add_argument('--field'); p.add_argument('--value', help='Typed JSON equality value')
    args = p.parse_args()
    if args.ledger:
        if not args.field or args.value is None: p.error('--field and --value required with a ledger')
        result = audit([json.loads(s) for s in args.ledger.read_text().splitlines() if s.strip()], args.field, json.loads(args.value))
        print(json.dumps(result, indent=2, allow_nan=False))
    else:
        root = Path(__file__).resolve().parent
        result = demonstrate(root)
        (root / 'coherence_results.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
        for field, report in result.items():
            print(field, 'cycles', report['orders']['common_gap']['cycle_count'], '/', report['triple_count'], 'global support', report['global_common_count'])
