"""Regression for extreme JSON numbers producing a report, not a crash."""
import json
import tempfile
import unittest
from pathlib import Path
from check_ledger import check

class CheckerTests(unittest.TestCase):
    def test_extreme_grade_and_scale_are_reported(self):
        for grade,scale in [(10**400,[0,1]),(.5,[0,10**400])]:
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'ledger.jsonl'
                p.write_text(json.dumps({'id':'x','native_score':grade,'score_available':True,'score_scale':scale})+'\n')
                report=check(p,['id'])
                self.assertFalse(report['valid'])
                self.assertGreater(sum(report['issue_counts'].values()),0)

if __name__=='__main__':unittest.main()
