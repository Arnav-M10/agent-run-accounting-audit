"""Optimistic query lower bounds for fixed-roster strict-order recovery.

Queries reveal one presently unavailable grade in the declared range. This
diagnostic supplies no outcomes, recommended query order, or guaranteed budget.
"""
import argparse
import json
import math
from pathlib import Path

from bounded_comparison import TOL, report_selected


def _minimum_possible(lower, upper, leverage, missing):
    """Return directional minima under maximally favorable query outcomes."""
    positive = negative = None
    for count in range(missing + 1):
        if positive is None and lower + count * leverage > TOL:
            positive = count
        if negative is None and upper - count * leverage < -TOL:
            negative = count
        if positive is not None and negative is not None:
            break
    possible = [x for x in (positive, negative) if x is not None]
    return (min(possible) if possible else None), positive, negative


def report_recovery(rows, tasks, models, scale=(0, 1)):
    """Describe recovery leverage for equal weights on a common task roster.

    Omitted records and explicit unavailable records both designate queryable
    slots. A query must reveal a valid score for exactly one such slot; this
    function never executes queries or assigns hypothetical scores to the ledger.
    """
    rows = list(rows)
    selected = report_selected(rows, tasks, models, scale)
    # Divide before subtracting to avoid needless range-width overflow.
    leverage = scale[1] / len(tasks) - scale[0] / len(tasks)
    if not math.isfinite(leverage) or leverage <= 0:
        raise ValueError('Nonfinite or unrepresentable per-slot leverage')
    available = {(r['model'], r['task_id']) for r in rows
                 if r['score_available']}
    unavailable = {m: [t for t in tasks if (m, t) not in available]
                   for m in models}
    pairs = []
    for pair in selected['pairs']:
        a, b = pair['models']
        slots = [{'model': m, 'task_id': t,
                  'maximum_interval_width_reduction': leverage}
                 for m in (a, b) for t in unavailable[m]]
        minimum, positive, negative = _minimum_possible(
            *pair['gap_bounds'], leverage, len(slots))
        status = ('already_certified' if pair['status'] == 'certified_order'
                  else 'strict_certification_impossible' if minimum is None
                  else 'strict_certification_possible')
        pairs.append(dict(pair, unavailable_slots=slots,
                          unavailable_slot_count=len(slots),
                          recovery_status=status,
                          optimistic_minimum_queries=minimum,
                          optimistic_queries_for_first_over_second=positive,
                          optimistic_queries_for_second_over_first=negative))
    return {
        'models': selected['models'], 'pairs': pairs,
        'score_range': list(scale), 'roster_size': len(tasks),
        'strict_tolerance': TOL,
        'per_slot_maximum_interval_width_reduction': leverage,
        'interpretation': (
            'Optimistic lower bound for possible strict certification under '
            'maximally favorable valid recovered grades; not a guaranteed '
            'query budget or an optimal recovery policy. Equal weights and '
            'the same declared roster apply to every model. Every unavailable '
            'slot has the same a priori interval-width leverage, so these '
            'bounds imply no unique query priority. Query counts are pairwise, '
            'not a simultaneous all-pairs budget: favorable outcomes for '
            'different pairwise claims may conflict. Null query '
            'minima mean strict certification is impossible within the '
            'declared unavailable slots and score range. No outcomes are '
            'fabricated, and unavailable scores are not failures.')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ledger', help='Selected-score ledger in JSONL format')
    parser.add_argument('--roster', required=True,
                        help='JSON object with tasks and models lists')
    parser.add_argument('--score-range', nargs=2, type=float, default=[0, 1])
    args = parser.parse_args()
    roster = json.loads(Path(args.roster).read_text())
    rows = [json.loads(line) for line in Path(args.ledger).read_text().splitlines()
            if line.strip()]
    print(json.dumps(report_recovery(rows, roster['tasks'], roster['models'],
                                     args.score_range), indent=2,
                     allow_nan=False))


if __name__ == '__main__':
    main()
