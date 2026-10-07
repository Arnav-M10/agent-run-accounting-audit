import itertools
import unittest
from fractions import Fraction
from oracle_opportunity_audit import thinning_probability, audit
from bounded_comparison import report_selected

class OracleTests(unittest.TestCase):
    def test_formula_matches_every_four_pass_subset(self):
        for rewards in itertools.product([0,1],repeat=4):
            for k in range(5):
                subsets=list(itertools.combinations(range(4),k))
                brute=Fraction(sum(any(rewards[i] for i in subset) for subset in subsets),len(subsets))
                self.assertEqual(thinning_probability(sum(rewards),k),brute)
    def test_unsupported_positive_k_remains_unknown(self):
        attempts=[];slots=[]
        for p in range(1,5):
            attempts.append({'attempt_id':str(p),'model':'M','domain':'D','task_id':'T','pass':p,'retention':'retained' if p<=2 else 'removed_incomplete','native_score':int(p==1),'score_scale':[0,1],'score_available':True})
            slots.append({'model':'M','domain':'D','task_id':'T','pass':p,'observed_attempt_id':str(p)})
        out=audit(attempts,slots)
        self.assertEqual(out['supported_summary']['groups'],0)
        self.assertIsNone(out['supported_summary']['thinned_probability'])
        self.assertIsNone(out['unsupported_cells'][0]['thinned_reference_probability'])
    def test_invalid_counts_rejected(self):
        for s,k in [(True,1),(2,1.5),(-1,3),(2,5)]:
            with self.assertRaises(ValueError):thinning_probability(s,k)
    def test_exact_tie_distinct_from_overlapping_unknown_bounds(self):
        rows=[{'model':m,'task_id':'t','score_scale':[0,1],'score_available':True,'native_score':0} for m in ['A','B']]
        tied=report_selected(rows,['t'],['A','B'])
        self.assertEqual(tied['pairs'][0]['status'],'exact_tie')
        unknown=report_selected(rows[:1],['t'],['A','B'])
        self.assertEqual(unknown['pairs'][0]['status'],'unresolved')

if __name__=='__main__':unittest.main()
