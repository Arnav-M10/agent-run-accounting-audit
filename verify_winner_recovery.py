import itertools,json
import winner_recovery as m
assert m.tests()==150
cases=unique=ties=policy=0
for vals in itertools.product((0,1),repeat=6):
    g=[list(vals[i:i+2]) for i in range(0,6,2)]
    sums=[sum(x) for x in g];w=max(range(3),key=sums.__getitem__)
    strict=sum(v==sums[w] for v in sums)==1
    for bits in itertools.product((False,True),repeat=6):
        masks=[list(bits[i:i+2]) for i in range(0,6,2)]
        o=m.optimal(g,masks,w);b=m.brute(g,masks,w)
        assert (None if o is None else o['count'])==b,(g,masks,o,b)
        if strict:
            unique+=1
            a=m.adaptive(g,masks,['A','B','C'],['1','2'])
            assert a['certified_winner']==['A','B','C'][w]
            assert o['count']<=a['queries']<=sum(not x for mask in masks for x in mask)
            policy+=1
        else:
            ties+=1;assert o is None
            assert m.adaptive(g,masks,['A','B','C'],['1','2'])['certified_winner'] is None
        cases+=1
result={'exhaustive_binary_3_models_2_tasks_all_64_masks_for_each_64_grade_arrays':cases,'strict_winner_cases':unique,'tied_winner_cases':ties,'policy_checked_strict_winner_cases':policy,'random_fractional_3_by_3_bruteforce_cases':150}
# No default writes: verifier prints its result only.

print(result)

g=[[.4999999999993,.4999999999993],[.4999999999995,.4999999999996],[.5000000000003,.5000000000008]]
masks=[[True,False],[False,True],[False,False]]
assert m.optimal(g,masks,2) is None  # exact gap equals tolerance, never strict
# Just above tolerance supports a certificate and rebuilt exact bounds agree.
g[2][1]=.5000000000009
assert m.optimal(g,masks,2)['count']==m.brute(g,masks,2)
print('Near-tolerance regression and above-tolerance certificate passed')
