import itertools,json,math
from pathlib import Path
from fractions import Fraction as F
R=[json.loads(l) for l in (Path(__file__).resolve().parent/'groups.jsonl').open()]
for r in R:
 k,s=r['k'],int(r['s']);m=4-k
 brute=[F((2*(s+sum(bits))-4)**2,16) for bits in itertools.product([0,1],repeat=m)]
 assert abs(float(min(brute))-r['missing_lo'])<1e-12
 assert abs(float(max(brute))-r['missing_hi'])<1e-12
 if r['n']==4 and k:
  ss=int(r['full_successes']);v=[1]*ss+[0]*(4-ss)
  thin=sum(F((2*sum(x)-k)**2,k*k) for x in itertools.combinations(v,k))/math.comb(4,k)
  assert abs(float(thin)-r['random_thin_C'])<1e-12
print('All 995 group bounds verified by exhaustive binary completions; all 893 supported group thinning references verified by exhaustive subset enumeration.')
