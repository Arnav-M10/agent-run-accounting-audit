"""Focused checks for missing evidence, typed rules, scales, and source preservation."""
import argparse
import json
from pathlib import Path
import tempfile
import unittest
from summarize_ledger import parse_rule, summarize


class LedgerTests(unittest.TestCase):
    def report(self, rows, rules=(), policy='exclude'):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ledger.jsonl'
            original = '\n'.join(json.dumps(row) for row in rows) + '\n'
            path.write_text(original)
            result = summarize(path, ['model'], rules, policy)
            self.assertEqual(path.read_text(), original)
            return result['groups']

    def test_null_and_absence_with_missing_policies(self):
        rows = [{'model': 'a', 'native_score': 0.6, 'score_scale': [0, 1]},
                {'model': 'a', 'native_score': None, 'score_scale': [0, 1]}, {'model': 'a'}]
        group = self.report(rows)[0]
        self.assertEqual((group['scored_count'], group['null_score_count'], group['absent_score_count']), (1, 1, 1))
        self.assertEqual(group['policy_score_mean'], 0.6)
        self.assertAlmostEqual(self.report(rows, policy='zero')[0]['policy_score_mean'], 0.2)
        with self.assertRaises(ValueError):
            self.report(rows, policy='error')

    def test_typed_equality_and_explicit_null(self):
        rows = [{'model': 'a', 'status': None}, {'model': 'a'},
                {'model': 'a', 'status': False}, {'model': 'a', 'status': 0}]
        for row in rows: row.update(native_score=None, score_scale=None)
        self.assertEqual(self.report(rows, [('status', None)])[0]['population_count'], 1)
        self.assertEqual(self.report(rows, [('status', 0)])[0]['population_count'], 1)

    def test_group_null_and_absence_are_distinct(self):
        groups = self.report([{'model': None, 'native_score': None, 'score_scale': None}, {'native_score': None, 'score_scale': None}])
        self.assertEqual(len(groups), 2)
        self.assertEqual({g['group'][0]['present'] for g in groups}, {True, False})

    def test_reject_invalid_scores_and_scales_even_if_excluded(self):
        for score, scale in [(True, [0, 1]), ('0.5', [0, 1]), (float('nan'), [0, 1]),
                             (float('inf'), [0, 1]), (2, [0, 1]), (0.5, None), (0.5, [1, 0])]:
            with self.subTest(score=score, scale=scale), self.assertRaises(ValueError):
                self.report([{'model': 'a', 'native_score': score, 'score_scale': scale, 'status': 'excluded'}], [('status', 'included')])

    def test_reject_mixed_scales(self):
        with self.assertRaises(ValueError):
            self.report([{'model': 'a', 'native_score': 0.5, 'score_scale': [0, 1]},
                         {'model': 'a', 'native_score': 5, 'score_scale': [0, 10]}])

    def test_zero_assignment_outside_scale_is_rejected(self):
        with self.assertRaises(ValueError):
            self.report([{'model': 'a', 'native_score': 2, 'score_scale': [1, 5]},
                         {'model': 'a', 'native_score': None, 'score_scale': [1, 5]}], policy='zero')

        with self.assertRaises(ValueError):
            self.report([{'model': 'a', 'native_score': None}], policy='zero')

    def test_unknown_score_override_cannot_silently_assign_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'ledger.jsonl'
            p.write_text(json.dumps({'model': 'a', 'native_score': .5, 'score_scale': [0, 1]})+'\n')
            with self.assertRaises(ValueError):
                summarize(p, ['model'], [], 'zero', score_field='native_socre')
            with self.assertRaises(ValueError):
                summarize(p, ['model'], [], 'exclude', scale_field='typo_scale')

    def test_known_failure_and_unknown_empty_support(self):
        rows = [{'model': 'error', 'parse_error': True, 'native_score': 0, 'score_scale': [0, 1]},
                {'model': 'unknown', 'parse_error': None, 'native_score': 1, 'score_scale': [0, 1]}]
        groups = {g['group'][0]['value']: g for g in self.report(rows, [('parse_error', False)])}
        for g in groups.values():
            self.assertEqual(g['population_count'], 0)
            self.assertIsNone(g['policy_score_mean'])
            self.assertEqual(g['unknown_score_count'], 0)
        self.assertEqual((groups['error']['known_ineligible_count'], groups['error']['unknown_eligibility_count']), (1, 0))
        self.assertEqual((groups['unknown']['known_ineligible_count'], groups['unknown']['unknown_eligibility_count']), (0, 1))

    def test_conjunction_false_dominates_unknown(self):
        # Enumerate true, false, explicit null and absent metadata for both rules.
        rows = []
        for a in range(4):
            for b in range(4):
                r = {'model': 'a', 'native_score': 1, 'score_scale': [0, 1]}
                for field, state in [('left', a), ('right', b)]:
                    if state < 3: r[field] = [True, False, None][state]
                rows.append(r)
        g = self.report(rows, [('left', True), ('right', True)])[0]
        self.assertEqual((g['population_count'], g['known_ineligible_count'], g['unknown_eligibility_count']), (1, 7, 8))
        self.assertEqual(g['excluded_count'], 15)
        self.assertEqual(g['policy_score_mean'], 1)
        for r in g['inclusion_rule_counts']:
            self.assertEqual([r[k] for k in ['matched_count', 'known_mismatch_count', 'null_unknown_count', 'absent_unknown_count']], [4, 4, 4, 4])

    def test_explicit_null_is_a_declared_selection_value(self):
        rows = [{'model': 'a', 'status': None}, {'model': 'a'},
                {'model': 'a', 'status': False}, {'model': 'a', 'status': 0}]
        for r in rows: r.update(native_score=1, score_scale=[0, 1])
        g = self.report(rows, [('status', None)])[0]
        self.assertEqual((g['population_count'], g['known_ineligible_count'], g['unknown_eligibility_count']), (1, 2, 1))
        self.assertEqual(g['inclusion_rule_counts'][0]['null_unknown_count'], 0)
        self.assertEqual(g['inclusion_rule_counts'][0]['absent_unknown_count'], 1)

    def test_rule_errors(self):
        for rule in ['status!=null', 'status>0', 'status=[1]', 'status=NaN', 'status=1e999']:
            with self.subTest(rule=rule), self.assertRaises(argparse.ArgumentTypeError):
                parse_rule(rule)
        with self.assertRaises(ValueError):
            self.report([{'model': 'a'}], [('typo', None)])


if __name__ == '__main__':
    unittest.main()
