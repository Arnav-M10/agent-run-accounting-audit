import itertools
import random
import unittest
from bounded_comparison import bounds, compare, report_selected
from mask_reference_audit import geometry, permute_masks, metrics, structure, audit

class ExtensionTests(unittest.TestCase):
    def test_bounds_sharp_by_exhaustive_binary_completions(self):
        known=[.3,.8]
        lo,hi=bounds(known,5)
        completions=[sum(known+list(x))/5 for x in itertools.product([0,1],repeat=3)]
        self.assertAlmostEqual(lo,min(completions));self.assertAlmostEqual(hi,max(completions))
    def test_no_false_certification_over_all_completions(self):
        ia=bounds([.8,.9],3);ib=bounds([.1,.1],3)
        _,order=compare(ia,ib);self.assertEqual(order,1)
        for a,b in itertools.product([0,1],repeat=2):
            self.assertGreater((1.7+a)/3,(.2+b)/3)
        self.assertEqual(compare(bounds([.8],3),bounds([.1],3))[1],0)
    def test_full_coverage_collapses_and_invalid_score_rejected(self):
        self.assertEqual(bounds([0,1],2),(.5,.5))
        for bad in [float('nan'),float('inf'),1.1]:
            with self.assertRaises(ValueError):bounds([bad],2)
    def test_joint_permutation_preserves_geometry_and_category_dependence(self):
        masks=[[1,0,1,0,1,0],[0,1,1,1,0,0],[1,1,0,0,1,1]]
        cats=[[0,1,2],[3,4,5]];expected=geometry(masks,cats)
        rng=random.Random(8)
        for _ in range(100):
            new=permute_masks(masks,cats,rng)
            self.assertEqual(geometry(new,cats),expected)
            for cat in cats:
                self.assertEqual(sorted(tuple(m[i] for m in masks) for i in cat),sorted(tuple(m[i] for m in new) for i in cat))
    def test_complete_roster_has_zero_selection_distortion(self):
        out=metrics([[.9,.7,.5],[.8,.6,.4],[.7,.5,.3]],[[True]*3]*3)
        self.assertEqual(out['common_reversals'],0);self.assertEqual(out['cyclic_triples'],0)
        self.assertAlmostEqual(out['mean_absolute_common_gap_displacement_points'],0)

class SelectedInputTests(unittest.TestCase):
    def test_missing_rows_and_null_grades_bound_declared_roster(self):
        rows=[{'model':'A','task_id':'t1','score_available':True,'native_score':.9,'score_scale':[0,1]},
              {'model':'B','task_id':'t1','score_available':False,'native_score':None,'score_scale':[0,1]}]
        out=report_selected(rows,['t1','t2'],['A','B'])
        self.assertEqual(out['models']['A']['known'],1)
        self.assertEqual(out['models']['A']['upper'],.95)
        self.assertEqual(out['models']['B']['upper'],1)
        self.assertIsNone(out['pairs'][0]['certified_order'])
    def test_duplicate_outside_roster_and_mixed_scale_rejected(self):
        row={'model':'A','task_id':'t1','score_available':True,'native_score':.9,'score_scale':[0,1]}
        for rows in [[row,row],[dict(row,task_id='t3')],[dict(row,score_scale=[0,10])]]:
            with self.assertRaises(ValueError):report_selected(rows,['t1','t2'],['A','B'])
    def test_reference_duplicate_and_partial_availability_rejected(self):
        row={'model':'A','task_id':'t1','flag':True}
        for rows in [[row,row],[row,dict(row,task_id='t2',flag=None)]]:
            with self.assertRaises(ValueError):structure(rows,'flag',True)

class StrictInputTests(unittest.TestCase):
    def test_alternative_blocks_preserve_observed_metrics(self):
        rows=[]
        for m in ['A','B']:
            for i in range(4):
                selected=(i != (0 if m=='A' else 3))
                rows.append({'model':m,'task_id':'01_task_'+str(i),'score_available':True,'native_score':(.2*i + (.1 if m=='A' else 0)),'score_scale':[0,1],'last_original_role':'assistant' if selected else 'user','native_stop_reason':'stop' if selected else None,'execution_status':'completed' if selected else 'error'})
        a=audit(rows,draws=2);b=audit(rows,draws=2,block_by='category_difficulty')
        for rule in a['rules']:
            self.assertEqual(b['rules'][rule]['category_sizes'],[4])
            self.assertEqual(b['rules'][rule]['block_sizes'],[2,2])
            for metric in a['rules'][rule]['metrics']:
                self.assertEqual(a['rules'][rule]['metrics'][metric]['observed'],b['rules'][rule]['metrics'][metric]['observed'])

    def test_invalid_draw_count_rejected(self):
        for count in [0,-1,1.5,True]:
            with self.assertRaises(ValueError):audit([],draws=count)
    def test_fractional_roster_boolean_and_nonfinite_range_rejected(self):
        for known,total,scale in [([.5],2.5,(0,1)),([True],2,(0,1)),([.5],2,(0,float('inf')))]:
            with self.assertRaises(ValueError):bounds(known,total,scale)
        with self.assertRaises(ValueError):compare((.9,.1),(0,1))
        with self.assertRaises(ValueError):compare((0,float('inf')),(0,1))
    def test_unknown_rule_model_and_empty_ledger_rejected(self):
        with self.assertRaises(ValueError):structure([],'flag',True)
        with self.assertRaises(ValueError):structure([{'model':'A','task_id':'t1','flag':None}],'flag',True)
    def test_boolean_grade_and_nonboolean_availability_rejected(self):
        rows=[{'model':m,'task_id':'t1','flag':True,'score_scale':[0,1],'score_available':True,'native_score':.5} for m in ['A','B']]
        for key,value in [('native_score',True),('score_available',1)]:
            bad=[dict(r) for r in rows];bad[0][key]=value
            with self.assertRaises(ValueError):structure(bad,'flag',True)

if __name__=='__main__':unittest.main()
