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

    def test_existing_but_wrong_task_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'slots.jsonl';q=Path(d)/'attempts.jsonl'
            q.write_text(json.dumps({'attempt_id':'a','task_id':'first'})+'\n'+json.dumps({'attempt_id':'b','task_id':'second'})+'\n')
            p.write_text(json.dumps({'slot':'first','task_id':'first','observed_attempt_id':'b'})+'\n')
            r=check(p,['slot'],q,match_reference_fields=['task_id'],unique_references=True)
            self.assertFalse(r['valid']);self.assertEqual(r['issue_counts']['reference_metadata_mismatch'],1)

    def test_reference_injectivity_and_unobserved_slots(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'slots.jsonl';q=Path(d)/'attempts.jsonl'
            q.write_text(json.dumps({'attempt_id':'a','task_id':'same'})+'\n')
            rows=[{'slot':1,'task_id':'same','observed_attempt_id':'a'}, {'slot':2,'task_id':'same','observed_attempt_id':'a'}, {'slot':3,'task_id':'absent','observed_attempt_id':None}]
            p.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            r=check(p,['slot'],q,match_reference_fields=['task_id'],unique_references=True)
            self.assertFalse(r['valid']);self.assertEqual(r['issue_counts'],{'duplicate_reference':1})
            p.write_text(json.dumps(rows[0])+'\n'+json.dumps(rows[2])+'\n')
            self.assertTrue(check(p,['slot'],q,match_reference_fields=['task_id'],unique_references=True)['valid'])

    def test_reference_agreement_requires_present_fields_and_configuration(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'slots.jsonl';q=Path(d)/'attempts.jsonl'
            p.write_text(json.dumps({'slot':1,'observed_attempt_id':'a'})+'\n');q.write_text(json.dumps({'attempt_id':'a','task_id':'x'})+'\n')
            r=check(p,['slot'],q,match_reference_fields=['task_id'])
            self.assertFalse(r['valid']);self.assertEqual(r['issue_counts']['reference_match_field_absent'],1)
            with self.assertRaises(ValueError):check(p,['slot'],match_reference_fields=['task_id'])

if __name__=='__main__':unittest.main()
