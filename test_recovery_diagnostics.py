import itertools
import unittest

from bounded_comparison import TOL, report_selected
from recovery_diagnostics import report_recovery


def row(model, task, score, scale=(0, 1)):
    return {'model': model, 'task_id': task, 'score_available': score is not None,
            'native_score': score, 'score_scale': list(scale)}


class RecoveryTests(unittest.TestCase):
    def test_optimistic_minimum_matches_exhaustive_binary_recovery(self):
        # Independently enumerate every observed/missing pattern through N=3,
        # every queried subset, and every binary query outcome. The first
        # possible certificate is the optimistic minimum, not a guarantee.
        for n in range(1, 4):
            tasks = list(range(n))
            identities = list(itertools.product(['A', 'B'], tasks))
            for scores in itertools.product([None, 0, 1], repeat=2 * n):
                rows = [row(m, t, s) for (m, t), s in zip(identities, scores)]
                missing = [i for i, score in enumerate(scores) if score is None]
                actual = None
                for count in range(len(missing) + 1):
                    found = False
                    for subset in itertools.combinations(missing, count):
                        for outcomes in itertools.product([0, 1], repeat=count):
                            recovered = [dict(r) for r in rows]
                            for i, score in zip(subset, outcomes):
                                recovered[i] = row(*identities[i], score)
                            if report_selected(recovered, tasks, ['A', 'B'])['pairs'][0]['certified_order']:
                                found = True
                                break
                        if found:
                            break
                    if found:
                        actual = count
                        break
                result = report_recovery(rows, tasks, ['A', 'B'])['pairs'][0]
                self.assertEqual(result['optimistic_minimum_queries'], actual,
                                 (n, scores))

    def test_bound_is_not_guaranteed_budget(self):
        tasks = ['t1', 't2']
        rows = [row('A', 't1', 1), row('B', 't1', 0),
                row('A', 't2', None), row('B', 't2', None)]
        result = report_recovery(rows, tasks, ['A', 'B'])['pairs'][0]
        self.assertEqual(result['optimistic_minimum_queries'], 1)
        # The adverse first query leaves the interval unresolved.
        rows[2] = row('A', 't2', 0)
        self.assertEqual(report_selected(rows, tasks, ['A', 'B'])['pairs'][0]['status'], 'unresolved')
        rows[3] = row('B', 't2', 1)
        self.assertEqual(report_recovery(rows, tasks, ['A', 'B'])['pairs'][0]['status'], 'exact_tie')

    def test_certified_exact_tie_and_small_gap(self):
        for scores, expected, status in [([1, 0], 0, 'already_certified'),
                                          ([.5, .5], None, 'strict_certification_impossible'),
                                          ([TOL / 2, 0], None, 'strict_certification_impossible')]:
            out = report_recovery([row('A', 't', scores[0]), row('B', 't', scores[1])], ['t'], ['A', 'B'])['pairs'][0]
            self.assertEqual(out['optimistic_minimum_queries'], expected)
            self.assertEqual(out['recovery_status'], status)

    def test_omitted_null_slots_and_declared_range(self):
        rows = [row('A', 'x', 4, (-2, 4)), row('B', 'y', None, (-2, 4))]
        result = report_recovery(rows, ['x', 'y'], ['A', 'B'], (-2, 4))
        pair = result['pairs'][0]
        self.assertEqual(pair['unavailable_slot_count'], 3)
        self.assertEqual([(s['model'], s['task_id']) for s in pair['unavailable_slots']], [('A', 'y'), ('B', 'x'), ('B', 'y')])
        self.assertTrue(all(s['maximum_interval_width_reduction'] == 3 for s in pair['unavailable_slots']))
        self.assertEqual(pair['optimistic_minimum_queries'], 2)

    def test_invalid_inputs_reuse_selected_validation(self):
        valid = row('A', 't', .5)
        cases = [([valid, valid], ['t'], ['A', 'B'], (0, 1)),
                 ([dict(valid, model='C')], ['t'], ['A', 'B'], (0, 1)),
                 ([dict(valid, task_id='other')], ['t'], ['A', 'B'], (0, 1)),
                 ([dict(valid, score_scale=[0, 10])], ['t'], ['A', 'B'], (0, 1)),
                 ([dict(valid, score_available=1)], ['t'], ['A', 'B'], (0, 1)),
                 ([dict(valid, native_score=True)], ['t'], ['A', 'B'], (0, 1)),
                 ([dict(valid, native_score=float('nan'))], ['t'], ['A', 'B'], (0, 1)),
                 ([dict(valid, native_score=2)], ['t'], ['A', 'B'], (0, 1)),
                 ([dict(valid, score_available=False)], ['t'], ['A', 'B'], (0, 1)),
                 ([], [], ['A', 'B'], (0, 1)),
                 ([], ['t', 't'], ['A', 'B'], (0, 1)),
                 ([], ['t'], ['A', 'A'], (0, 1)),
                 ([], ['t'], ['A'], (0, 1)),
                 ([], ['t'], ['A', 'B'], (0, float('inf'))),
                 ([], ['t'], ['A', 'B'], (False, True)),
                 ([], ['t'], ['A', 'B'], (1, 0))]
        for rows, tasks, models, scale in cases:
            with self.subTest(rows=rows, tasks=tasks, models=models, scale=scale):
                with self.assertRaises(ValueError):
                    report_recovery(rows, tasks, models, scale)


if __name__ == '__main__':
    unittest.main()
