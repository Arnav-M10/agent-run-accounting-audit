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
        self.assertEqual(self.report(rows, [('status', None)])[0]['population_count'], 1)
        self.assertEqual(self.report(rows, [('status', 0)])[0]['population_count'], 1)

    def test_group_null_and_absence_are_distinct(self):
        groups = self.report([{'model': None}, {}])
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

    def test_rule_errors(self):
        for rule in ['status!=null', 'status>0', 'status=[1]', 'status=NaN']:
            with self.subTest(rule=rule), self.assertRaises(argparse.ArgumentTypeError):
                parse_rule(rule)
        with self.assertRaises(ValueError):
            self.report([{'model': 'a'}], [('typo', None)])


if __name__ == '__main__':
    unittest.main()
