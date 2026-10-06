import unittest
from common_support_audit import compare

def row(m,t,x,keep=True):
    return dict(model=m,task_id=t,native_score=x,score_available=True,score_scale=[0,1],keep=keep)

class SupportTests(unittest.TestCase):
    def test_reversal_disappears_on_common(self):
        rows=[row('A','1',.6),row('A','2',1),row('A','3',0,False),
              row('B','1',.7),row('B','2',1,False),row('B','3',.4)]
        p=compare(rows,'keep',True)['pairs'][0]
        self.assertEqual(p['reversal_class'],'disappears_on_common')
        self.assertAlmostEqual(p['common_gap'],-.1)
        self.assertAlmostEqual(p['separate_shift'],p['common_support_shift']+p['different_support_component'])
    def test_reversal_persists(self):
        rows=[row('A','1',1),row('A','2',0,False),row('B','1',.6),row('B','2',1,False)]
        self.assertEqual(compare(rows,'keep',True)['pairs'][0]['reversal_class'],'persists_on_common')
    def test_empty_intersection_is_undefined(self):
        rows=[row('A','1',1),row('A','2',0,False),row('B','1',1,False),row('B','2',.6)]
        p=compare(rows,'keep',True)['pairs'][0]
        self.assertIsNone(p['common_gap']); self.assertEqual(p['reversal_class'],'undefined_common')
    def test_numeric_equality_matches_json_numbers_but_not_bools(self):
        p=compare([row('A','1',.2,1),row('B','1',.5,1.0)],'keep',1)['pairs'][0]
        self.assertEqual((p['selected_a_count'],p['selected_b_count']),(1,1))
        self.assertIsNone(compare([row('A','1',.2,True),row('B','1',.5,1)],'keep',1)['pairs'][0]['separate_gap'])

    def test_empty_selected_population_is_not_a_nonreversal(self):
        result=compare([row('A','1',.2,False),row('B','1',.5,False)],'keep',True)
        p=result['pairs'][0]
        self.assertIsNone(p['separate_reversal']); self.assertIsNone(p['common_reversal'])
        self.assertEqual(p['reversal_class'],'undefined_separate')
        self.assertEqual(result['undefined_separate_pairs'],1)
        self.assertEqual(result['classification_counts']['not_reversed'],0)

    def test_refuses_missing_grade_roster_scale_and_duplicates(self):
        base=[row('A','1',.5),row('B','1',.5)]
        for rows in [base+[base[0]], [base[0],row('B','2',.5)],
                     [base[0],dict(base[1],native_score=None)],
                     [base[0],dict(base[1],score_scale=[0,10])]]:
            with self.assertRaises(ValueError):compare(rows,'keep',True)
    def test_absent_null_and_typed_equality(self):
        rows=[row('A','1',.5),row('B','1',.5)]
        rows[0]['keep']=None; del rows[1]['keep']
        p=compare(rows,'keep',None)['pairs'][0]
        self.assertEqual((p['selected_a_count'],p['selected_b_count']),(1,0))
        self.assertEqual(compare([row('A','1',.5,1),row('B','1',.5,True)],'keep',True)['pairs'][0]['selected_a_count'],0)

if __name__=='__main__': unittest.main()
