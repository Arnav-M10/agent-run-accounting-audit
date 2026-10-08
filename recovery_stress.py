"""Execute the frozen aggregate-only retrospective recovery stress experiment."""
import hashlib
import json
import math
import random
from fractions import Fraction
from pathlib import Path

from mask_reference_audit import structure
from winner_recovery import TOL, adaptive, bounds, exact, optimal

ROOT = Path(__file__).resolve().parent
RATES = (0.1, 0.25, 0.5)
SEEDS = 30


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summary(values):
    v = sorted(values)
    return {'count': len(v), 'mean': math.fsum(v)/len(v),
            'median': (v[(len(v)-1)//2]+v[len(v)//2])/2,
            'q05_nearest_rank': v[math.ceil(.05*len(v))-1],
            'q95_nearest_rank': v[math.ceil(.95*len(v))-1],
            'min': v[0], 'max': v[-1]}


def certificate(grades, masks):
    bb = [bounds([x for x, k in zip(g, mask) if k], len(g))
          for g, mask in zip(grades, masks)]
    winners = [m for m in range(len(grades))
               if all(bb[m][0]-bb[j][1] > TOL for j in range(len(grades)) if j != m)]
    assert len(winners) <= 1
    return winners[0] if winners else None


def retrieve_in_order(grades, masks, order):
    # Maintain exact interval endpoints; ordering never consults omitted grades.
    n = len(grades[0])
    totals = [sum((exact(x) for x, k in zip(g, mask) if k), Fraction(0))
              for g, mask in zip(grades, masks)]
    counts = [sum(not k for k in mask) for mask in masks]
    restored = []
    for slot in [None] + order:
        if slot is not None:
            m, t = slot
            totals[m] += exact(grades[m][t])
            counts[m] -= 1
            restored.append(slot)
        w = max(range(len(grades)), key=lambda m: totals[m])
        if all(totals[w]-totals[j]-counts[j] > n*TOL
               for j in range(len(grades)) if j != w):
            return restored, w
    return restored, None


def validate(grades, masks, restored, claimed, full_winners):
    updated = [list(mask) for mask in masks]
    assert len(set(restored)) == len(restored)
    for m, t in restored:
        assert not updated[m][t]
        updated[m][t] = True
    actual = certificate(grades, updated)
    assert actual == claimed
    if actual is not None:
        assert full_winners == [actual]


def experiment():
    ledger = ROOT/'run_accounting/wildclaw_released_pairs.jsonl'
    rows = [json.loads(x) for x in ledger.read_text().splitlines() if x.strip()]
    models, tasks, grades, _, _ = structure(rows, 'last_original_role', 'assistant')
    assert (len(models), len(tasks), len(rows)) == (12, 60, 720)
    means = [sum((exact(v) for v in g), Fraction(0))/len(tasks) for g in grades]
    full_winners = [m for m, mean in enumerate(means) if max(means)-mean <= TOL]
    model_index = {m: i for i, m in enumerate(models)}
    task_index = {t: i for i, t in enumerate(tasks)}
    methods = ('selector_blind', 'lexicographic', 'randomized', 'oracle', 'restore_all')
    output = {
        'frozen_plan_sha256': digest(ROOT/'recovery_stress_plan.md'),
        'program_sha256': digest(Path(__file__)),
        'input_sha256': digest(ledger),
        'winner_recovery_sha256': digest(ROOT/'winner_recovery.py'),
        'mask_reference_audit_sha256': digest(ROOT/'mask_reference_audit.py'),
        'model_count': len(models), 'task_count': len(tasks), 'cell_count': len(rows),
        'full_mean_maximizer_count': len(full_winners),
        'strict_tolerance': str(TOL), 'seeds_per_rate': SEEDS, 'case_count': SEEDS*len(RATES),
        'mask_seed_rule': '2026100800 + 1000 * zero_based_rate_index + seed_index',
        'retrieval_seed_rule': '2026101800 + 1000 * zero_based_rate_index + seed_index',
        'sampling': 'Independent Bernoulli omission at every cell; all cases retained without resampling.',
        'target': 'Unique strict maximizer of equally weighted full recorded-grade means.',
        'interpretation': 'Retrospective simulation on existing grades, not deployment or independent achievement validation. Oracle uses omitted truth and gives no prospective budget guarantee.',
        'rates': {}}
    for rate_index, rate in enumerate(RATES):
        costs = {method: [] for method in methods}
        certified = {method: 0 for method in methods}
        fractions = {method: [] for method in methods}
        omitted_counts, positive_counts = [], []
        initial_certificates = 0
        oracle_null = 0
        for seed in range(SEEDS):
            rng = random.Random(2026100800 + 1000*rate_index + seed)
            masks = [[rng.random() >= rate for _ in tasks] for _ in models]
            slots = [(m, t) for m, mask in enumerate(masks) for t, k in enumerate(mask) if not k]
            omitted_counts.append(len(slots))
            positive_counts.append(sum(exact(grades[m][t]) > 0 for m, t in slots if m in full_winners))
            initial_certificates += certificate(grades, masks) is not None
            policy = adaptive(grades, masks, models, tasks)
            restored = [(model_index[x['model']], task_index[x['task_id']]) for x in policy['log']]
            policy_w = model_index[policy['certified_winner']] if policy['certified_winner'] is not None else None
            validate(grades, masks, restored, policy_w, full_winners)
            case = {'selector_blind': (len(restored), policy_w)}
            for method in ('lexicographic', 'randomized'):
                order = slots.copy()
                if method == 'randomized':
                    random.Random(2026101800 + 1000*rate_index + seed).shuffle(order)
                restored, w = retrieve_in_order(grades, masks, order)
                validate(grades, masks, restored, w, full_winners)
                case[method] = (len(restored), w)
            w = certificate(grades, [[True]*len(tasks) for _ in models])
            validate(grades, masks, slots, w, full_winners)
            case['restore_all'] = (len(slots), w)
            oracle = optimal(grades, masks, full_winners[0]) if len(full_winners) == 1 else None
            if oracle is None:
                oracle_null += 1
                case['oracle'] = (None, None)
            else:
                validate(grades, masks, oracle['disclosures'], full_winners[0], full_winners)
                case['oracle'] = (oracle['count'], full_winners[0])
                assert all(oracle['count'] <= case[method][0] for method in methods if method != 'oracle')
            for method, (cost, w) in case.items():
                certified[method] += w is not None
                if cost is not None:
                    costs[method].append(cost)
                    fractions[method].append(cost/len(slots) if slots else 0)
        output['rates'][str(rate)] = {
            'cases': SEEDS, 'tied_full_winner_cases': SEEDS if len(full_winners) != 1 else 0,
            'initial_certificate_cases': initial_certificates,
            'omitted_grade_count': summary(omitted_counts),
            'positive_omitted_full_winner_grade_count': summary(positive_counts),
            'cases_with_positive_omitted_full_winner_grade': sum(v > 0 for v in positive_counts),
            'oracle_null_cases': oracle_null,
            'methods': {method: {'certificate_cases': certified[method],
                        'certificate_rate_all_cases': certified[method]/SEEDS,
                        'query_count_all_cases': summary(costs[method]) if costs[method] else None,
                        'fraction_omitted_retrieved': summary(fractions[method]) if fractions[method] else None}
                        for method in methods},
            'paired_selector_minus_baseline_queries': {
                method: summary([a-b for a, b in zip(costs['selector_blind'], costs[method])])
                for method in ('lexicographic', 'randomized', 'restore_all')},
            'paired_selector_minus_oracle_queries': {
                'nonnull_case_count': len(costs['oracle']),
                'summary': summary([a-b for a, b in zip(costs['selector_blind'], costs['oracle'])]) if costs['oracle'] else None},
            'selector_query_cost_cases_vs_baseline': {
                method: {'lower': sum(a < b for a, b in zip(costs['selector_blind'], costs[method])),
                         'equal': sum(a == b for a, b in zip(costs['selector_blind'], costs[method])),
                         'higher': sum(a > b for a, b in zip(costs['selector_blind'], costs[method]))}
                for method in ('lexicographic', 'randomized', 'restore_all')}}
    output['validation'] = {'all_cases_retained': True, 'case_count': SEEDS*len(RATES),
                            'all_certificates_checked_against_exact_full_means_and_intervals': True,
                            'oracle_cost_no_greater_than_every_policy_cost': True,
                            'published_raw_grade_or_identity_rows': False}
    return output


def main():
    first = experiment()
    second = experiment()
    assert json.dumps(first, sort_keys=True, allow_nan=False) == json.dumps(second, sort_keys=True, allow_nan=False)
    first['validation']['complete_repeat_canonical_aggregate_byte_identical'] = True
    (ROOT/'recovery_stress_results.json').write_text(json.dumps(first, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({rate: {method: (info['query_count_all_cases']['mean'] if info['query_count_all_cases'] else None)
                     for method, info in data['methods'].items()} for rate, data in first['rates'].items()}, indent=2))


if __name__ == '__main__':
    main()
