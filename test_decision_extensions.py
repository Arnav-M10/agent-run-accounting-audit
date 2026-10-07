import itertools
import random
import unittest
from bounded_comparison import bounds, compare
from mask_reference_audit import geometry, permute_masks, metrics

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

if __name__=='__main__':unittest.main()
