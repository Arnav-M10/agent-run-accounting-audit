"""Verify pinned inputs, then compare one fresh replay with saved outputs."""
import json
from reproduce import HERE, ROOT, METHODS, encoded, experiment, sha

for path,expected in json.loads((HERE/'source_hash_manifest.json').read_text()).items():
    assert sha(ROOT/path)==expected, path
fresh=encoded(*experiment())
assert fresh[0]==(HERE/'results.json').read_text()
assert fresh[1]==(HERE/'per_case.csv').read_bytes().decode()
new=json.loads(fresh[0])['wild_original']['rates']
old=json.loads((ROOT/'recovery_stress_results.json').read_text())['rates']
for rate,entry in old.items():
    for method in ('selector_blind','lexicographic','randomized','oracle','restore_all'):
        assert new[rate]['methods'][method]['costs_nonnull']==entry['methods'][method]['query_count_all_cases']
        assert new[rate]['methods'][method]['certificate_cases']==entry['methods'][method]['certificate_cases']
print('Pinned hashes, one fresh 270-case replay, saved CSV/results, independent final certificates, and unchanged original90 baseline summaries verified.')
