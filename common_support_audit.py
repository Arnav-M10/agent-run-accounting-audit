"""Describe pairwise score gaps with explicit, identical task support. No inference."""
import argparse
import json
import math
from itertools import combinations
from pathlib import Path

EPS = 1e-12

def sign(x):
    return 0 if abs(x) <= EPS else (1 if x > 0 else -1)

def compare(rows, field, value):
    groups = {}
    scale = None
    for row in rows:
        model, task = row['model'], row['task_id']
        if not isinstance(model, str) or not isinstance(task, str):
            raise ValueError('Model and task identities must be strings')
        score = row.get('native_score')
        declared = row.get('score_scale')
        if (not isinstance(declared, list) or len(declared) != 2
            or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in declared)
            or declared[0] >= declared[1]):
            raise ValueError('Finite increasing score scale required')
        if scale is None: scale = declared
        if declared != scale: raise ValueError('Mixed score scales')
        if (row.get('score_available') is not True or isinstance(score, bool)
            or not isinstance(score, (int, float)) or not math.isfinite(score)
            or not declared[0] <= score <= declared[1]):
            raise ValueError('Every supplied row requires an available in-range grade')
        group = groups.setdefault(model, {})
        if task in group: raise ValueError('Duplicate model-task identity')
        group[task] = row
    if not groups: raise ValueError('Empty ledger')
    if not any(field in r for r in rows): raise ValueError('Unknown predicate field')
    tasks = set(next(iter(groups.values())))
    if any(set(g) != tasks for g in groups.values()):
        raise ValueError('This reporter requires an identical fully scored task roster')
    # Absent fields never match; null matches only explicitly recorded null.
    selected = {m:{t for t,r in g.items() if field in r and type(r[field]) is type(value) and r[field] == value}
                for m,g in groups.items()}
    def mean(m, ts):
        return math.fsum(groups[m][t]['native_score'] for t in sorted(ts)) / len(ts)
    pairs = []
    for a,b in combinations(sorted(groups),2):
        sa,sb = selected[a],selected[b]
        common = sa & sb
        full = mean(a,tasks) - mean(b,tasks)
        separate = mean(a,sa) - mean(b,sb) if sa and sb else None
        matched = mean(a,common) - mean(b,common) if common else None
        row = {'model_a':a,'model_b':b,'full_count':len(tasks),
               'selected_a_count':len(sa),'selected_b_count':len(sb),
               'common_count':len(common),'selected_only_a_count':len(sa-common),
               'selected_only_b_count':len(sb-common),
               'full_gap':full,'separate_gap':separate,'common_gap':matched,
               'common_task_ids':sorted(common)}
        reversed_separate = separate is not None and sign(full)*sign(separate) < 0
        row['separate_reversal'] = reversed_separate
        row['common_reversal'] = matched is not None and sign(full)*sign(matched) < 0
        row['reversal_class'] = ('not_reversed' if not reversed_separate else
            'undefined_common' if matched is None else
            'tie_on_common' if sign(matched) == 0 else
            'persists_on_common' if row['common_reversal'] else 'disappears_on_common')
        if matched is not None and separate is not None:
            row['common_support_shift'] = matched-full
            row['different_support_component'] = separate-matched
            row['separate_shift'] = separate-full
            assert math.isclose(row['separate_shift'], row['common_support_shift']+row['different_support_component'], abs_tol=EPS)
        pairs.append(row)
    counts={k:sum(p['reversal_class']==k for p in pairs) for k in
            ['not_reversed','persists_on_common','disappears_on_common','tie_on_common','undefined_common']}
    return {'interpretation':'Recorded-grade contrasts on a fixed fully scored task roster. Common support changes the estimand; no causal attribution, general ranking, or outcome validation.',
            'predicate':{'field':field,'value':value},'score_scale':scale,'models':len(groups),
            'tasks_per_model':len(tasks),'pair_count':len(pairs),'classification_counts':counts,
            'empty_intersection_pairs':sum(p['common_count']==0 for p in pairs),
            'pairs':pairs}

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('ledger',type=Path); p.add_argument('--field',required=True)
    p.add_argument('--value',required=True,help='Typed JSON equality value')
    a=p.parse_args()
    rows=[json.loads(s) for s in a.ledger.read_text().splitlines() if s.strip()]
    print(json.dumps(compare(rows,a.field,json.loads(a.value)),indent=2,allow_nan=False))
