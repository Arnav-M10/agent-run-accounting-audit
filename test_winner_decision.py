import itertools
import unittest
from bounded_comparison import TOL
from winner_decision import report_winners


def row(m,t,s):return {'model':m,'task_id':t,'score_available':s is not None,'native_score':s,'score_scale':[0,1]}


class WinnerTests(unittest.TestCase):
    def test_candidates_and_certificates_match_all_small_completions(self):
        models=['A','B','C'];tasks=['x','y'];keys=list(itertools.product(models,tasks))
        for pattern in itertools.product([None,0,1],repeat=6):
            rows=[row(m,t,s) for (m,t),s in zip(keys,pattern)]
            missing=[i for i,x in enumerate(pattern) if x is None]
            possible=set();strict_in_every=set(models)
            for values in itertools.product([0,1],repeat=len(missing)):
                grades=list(pattern)
                for i,x in zip(missing,values):grades[i]=x
                means={m:sum(grades[i] for i,key in enumerate(keys) if key[0]==m)/2 for m in models}
                possible.update(m for m in models if max(means.values())-means[m]<=TOL)
                strict_in_every.intersection_update(m for m in models if all(means[m]-means[o]>TOL for o in models if o!=m))
            result=report_winners(rows,tasks,models)
            self.assertEqual(set(result['not_ruled_out_as_roster_maximizer']),possible)
            self.assertEqual(set(result['certified_strict_roster_maximizer']),strict_in_every)

    def test_selected_leader_need_not_be_roster_winner(self):
        rows=[row('A','x',1),row('A','y',None),row('B','x',.6),row('B','y',.6)]
        r=report_winners(rows,['x','y'],['A','B'])
        self.assertEqual(set(r['not_ruled_out_as_roster_maximizer']),{'A','B'})
        self.assertEqual(r['certified_strict_roster_maximizer'],[])
        rows[1]=row('A','y',0)
        self.assertEqual(report_winners(rows,['x','y'],['A','B'])['certified_strict_roster_maximizer'],['B'])

    def test_complete_tie_and_empty_model(self):
        tied=[row(m,'x',.5) for m in ['A','B']]
        r=report_winners(tied,['x'],['A','B'])
        self.assertEqual(r['not_ruled_out_as_roster_maximizer'],['A','B'])
        self.assertEqual(r['certified_strict_roster_maximizer'],[])
        missing=report_winners([row('A','x',.5)],['x'],['A','B'])
        self.assertEqual(missing['not_ruled_out_as_roster_maximizer'],['A','B'])

    def test_bad_identity_or_scale_rejected(self):
        for rows in [[row('A','x',.5),row('A','x',.5)], [row('C','x',.5)], [dict(row('A','x',.5),score_scale=[0,10])]]:
            with self.assertRaises(ValueError):report_winners(rows,['x'],['A','B'])


if __name__=='__main__':unittest.main()
