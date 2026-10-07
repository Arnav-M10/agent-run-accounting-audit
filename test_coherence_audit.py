import unittest
from coherence_audit import audit, directed_cycle

class CoherenceTests(unittest.TestCase):
    def rows(self):
        # Three disjoint pair intersections create A>B>C>A with fixed grades.
        selected = {'A': {'ab', 'ca'}, 'B': {'ab', 'bc'}, 'C': {'bc', 'ca'}}
        ones = {'A': 'ab', 'B': 'bc', 'C': 'ca'}
        return [{'model': m, 'task_id': t, 'native_score': int(ones[m] == t),
                 'score_scale': [0, 1], 'score_available': True, 'eligible': t in selected[m]}
                for m in selected for t in ['ab', 'bc', 'ca']]

    def test_cycle_certificate_and_empty_global_support(self):
        r = audit(self.rows(), 'eligible', True)
        self.assertEqual(r['orders']['common_gap']['cycle_count'], 1)
        self.assertEqual(r['orders']['full_gap']['cycle_count'], 0)
        self.assertEqual(r['orders']['separate_gap']['cycle_count'], 0)
        self.assertIsNone(r['global_common_means'])
        edges = r['orders']['common_gap']['cycles'][0]['edges']
        self.assertEqual([(e['winner'], e['loser']) for e in edges], [('A', 'B'), ('B', 'C'), ('C', 'A')])
        self.assertTrue(all(e['gap'] == 1 and e['common_count'] == 1 for e in edges))

    def test_small_cycle_disappears_above_declared_margin(self):
        rows = self.rows()
        for r in rows:
            if r['model'] == 'A' and r['task_id'] == 'ab': r['native_score'] = .003
        result = audit(rows, 'eligible', True)['orders']['common_gap']
        self.assertEqual(result['cycle_count'], 1)
        self.assertEqual([p['cycle_count'] for p in result['descriptive_margin_profile']], [1, 0, 0, 0])
        self.assertAlmostEqual(result['cycles'][0]['minimum_edge_gap'], .003)

    def test_four_cycle_without_triangles(self):
        graph = {'A': {'B'}, 'B': {'C'}, 'C': {'D'}, 'D': {'A'}}
        self.assertEqual(directed_cycle(graph), ['A', 'B', 'C', 'D', 'A'])
        graph['D'] = set()
        self.assertIsNone(directed_cycle(graph))

    def test_identical_support_is_coherent(self):
        rows = self.rows()
        for r in rows: r['eligible'] = True; r['native_score'] = {'A': 1, 'B': .5, 'C': 0}[r['model']]
        r = audit(rows, 'eligible', True)
        self.assertEqual(r['orders']['common_gap']['cycle_count'], 0)
        self.assertEqual(r['global_common_count'], 3)

    def test_undefined_pairs_are_not_ties(self):
        rows = self.rows()
        for r in rows: r['eligible'] = False
        r = audit(rows, 'eligible', True)
        self.assertEqual(r['orders']['common_gap']['undefined_edges'], 3)
        self.assertEqual(r['orders']['common_gap']['tied_edges'], 0)
        self.assertEqual(r['orders']['common_gap']['cycle_count'], 0)

if __name__ == '__main__': unittest.main()
