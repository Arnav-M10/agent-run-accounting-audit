"""Exploratory coverage-preserving completion-mask reference; no inference calls."""
import itertools
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOL = 1e-12


def structure(rows, field, value, allow_unknown_models=False):
    by_model = {}
    for row in rows:
        records = by_model.setdefault(row['model'], {})
        if row['task_id'] in records:
            raise ValueError('Duplicate model/task identity')
        records[row['task_id']] = row
    if not by_model:
        raise ValueError('Empty ledger')
    for rs in by_model.values():
        present = [r.get(field) is not None for r in rs.values()]
        if not any(present) and not allow_unknown_models:
            raise ValueError('Unknown rule fields for a model')
        if any(present) and not all(present):
            raise ValueError('Partially unknown rule fields within a model')
    models = sorted(m for m, rs in by_model.items()
                    if all(r.get(field) is not None for r in rs.values()))
    if len(models) < 2:
        raise ValueError('Requires at least two rule-covered models')
    tasks = sorted(by_model[models[0]])
    if any(set(by_model[m]) != set(tasks) for m in models):
        raise ValueError('Requires identical complete task rosters')
    if any(r['score_scale'] != [0, 1] or not r['score_available']
           or type(r['score_available']) is not bool
           or isinstance(r['native_score'], bool)
           or not isinstance(r['native_score'], (int, float))
           or not math.isfinite(r['native_score']) or not 0 <= r['native_score'] <= 1
           for m in models for r in by_model[m].values()):
        raise ValueError('Requires available finite grades on [0,1]')
    grades = [[by_model[m][t]['native_score'] for t in tasks] for m in models]
    masks = [[by_model[m][t][field] == value for t in tasks] for m in models]
    categories = {}
    for i, task in enumerate(tasks):
        categories.setdefault(task.split('_', 1)[0], []).append(i)
    return models, tasks, grades, masks, list(categories.values())


def permute_masks(masks, categories, rng):
    source = list(range(len(masks[0])))
    for indices in categories:
        shuffled = indices.copy()
        rng.shuffle(shuffled)
        for target, original in zip(indices, shuffled):
            source[target] = original
    return [[mask[i] for i in source] for mask in masks]


def geometry(masks, categories):
    return ([sum(mask[i] for i in cat) for mask in masks for cat in categories],
            [sum(a and b for a, b in zip(masks[i], masks[j]))
             for i, j in itertools.combinations(range(len(masks)), 2)],
            sum(all(mask[t] for mask in masks) for t in range(len(masks[0]))))


def metrics(grades, masks):
    n = len(grades)
    means = [math.fsum(g) / len(g) for g in grades]
    selected = [[i for i, ok in enumerate(mask) if ok] for mask in masks]
    if any(not s for s in selected):
        raise ValueError('Empty selected population')
    filtered = [math.fsum(grades[m][i] for i in selected[m]) / len(selected[m])
                for m in range(n)]
    separate = common = 0
    displacements = []
    edges = set()
    for a, b in itertools.combinations(range(n), 2):
        baseline = means[a] - means[b]
        filtered_gap = filtered[a] - filtered[b]
        support = [i for i in selected[a] if masks[b][i]]
        if not support:
            raise ValueError('Empty pair intersection')
        matched_gap = math.fsum(grades[a][i] - grades[b][i] for i in support) / len(support)
        displacements.append(abs(matched_gap-baseline))
        separate += abs(baseline) > TOL and abs(filtered_gap) > TOL and baseline * filtered_gap < 0
        common += abs(baseline) > TOL and abs(matched_gap) > TOL and baseline * matched_gap < 0
        if matched_gap > TOL:
            edges.add((a, b))
        elif matched_gap < -TOL:
            edges.add((b, a))
    cycles = sum(((a,b) in edges and (b,c) in edges and (c,a) in edges)
                 or ((a,c) in edges and (c,b) in edges and (b,a) in edges)
                 for a,b,c in itertools.combinations(range(n), 3))
    return {'mean_absolute_common_gap_displacement_points': 100 * math.fsum(displacements)/len(displacements),
            'max_absolute_shift_points': 100 * max(abs(x-y) for x,y in zip(filtered,means)),
            'separate_reversals': separate, 'common_reversals': common, 'cyclic_triples': cycles}


def audit(rows, draws=1999, seed=20261007, block_by="category"):
    if type(draws) is not int or draws <= 0:
        raise ValueError('Draw count must be a positive integer')
    if block_by not in ('category','category_difficulty'):
        raise ValueError('Unknown blocking scheme')
    result = {'draws': draws, 'seed': seed, 'block_by': block_by, 'interpretation':
              'Exploratory within-category joint-mask reference, not a causal or confirmatory significance test.', 'rules': {}}
    for name, field, value in [('assistant','last_original_role','assistant'),
                               ('native_stop','native_stop_reason','stop'),
                               ('exporter','execution_status','completed')]:
        # Missing native stop reason at non-assistant endings is known ineligible,
        # not unknown rule availability. Only exporter lacks model-level headers.
        working = [dict(r) for r in rows]
        if field == 'native_stop_reason':
            for row in working:
                if row.get(field) is None:
                    if row.get('last_original_role') == 'assistant':
                        raise ValueError('Unknown stop reason on assistant ending')
                    row[field] = '__no_assistant_stop_event__'
        models,tasks,grades,masks,categories = structure(working,field,value,allow_unknown_models=(name == 'exporter'))
        category_sizes=[len(c) for c in categories]
        if block_by == 'category_difficulty':
            blocks=[]
            for category in categories:
                ordered=sorted(category,key=lambda i:(math.fsum(g[i] for g in grades)/len(grades),tasks[i]))
                midpoint=len(ordered)//2
                blocks.extend([ordered[:midpoint],ordered[midpoint:]])
            categories=[c for c in blocks if c]
        original_geometry = geometry(masks,categories)
        observed = metrics(grades,masks)
        values = {key: [] for key in observed}
        rng = random.Random(seed)
        for _ in range(draws):
            permuted = permute_masks(masks,categories,rng)
            if geometry(permuted,categories) != original_geometry:
                raise AssertionError('Coverage or overlap changed')
            for key,val in metrics(grades,permuted).items():
                values[key].append(val)
        summaries = {}
        for key, sample in values.items():
            ordered = sorted(sample)
            summaries[key] = {'observed': observed[key],
                             'q05': ordered[math.ceil(.05*draws)-1],
                             'median': ordered[math.ceil(.5*draws)-1],
                             'q95': ordered[math.ceil(.95*draws)-1],
                             'draws_at_least_observed': sum(v >= observed[key]-TOL for v in sample)}
        result['rules'][name] = {'models': models, 'task_count': len(tasks),
                                'category_sizes': category_sizes, 'block_sizes': [len(c) for c in categories],
                                'coverage_geometry_preserved_in_every_draw': True,
                                'metrics': summaries}
    return result

if __name__ == '__main__':
    rows = [json.loads(line) for line in (ROOT/'run_accounting/wildclaw_released_pairs.jsonl').read_text().splitlines()]
    result = audit(rows)
    (ROOT/'mask_reference_results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v['metrics'] for k,v in result['rules'].items()},indent=2))
