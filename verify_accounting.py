"""Verify exported run accounting against the separately produced audit summaries."""
import json
import hashlib
import math
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / 'source_hashes.json').read_text())
for name, expected_hash in manifest.items():
    digest = hashlib.sha256()
    with (ROOT / name).open('rb') as handle:
        for chunk in iter(lambda: handle.read(2**20), b''):
            digest.update(chunk)
    assert digest.hexdigest() == expected_hash, name
def read(name):
    with (ROOT / 'run_accounting' / name).open() as handle:
        return [json.loads(line) for line in handle]

cmu = read('cmu_attempts.jsonl')
slots = read('cmu_search_slots.jsonl')
wild = read('wildclaw_released_pairs.jsonl')
cmu_result = json.loads((ROOT / 'audit_results.json').read_text())
wild_result = json.loads((ROOT / 'independent_results.json').read_text())
assert len(cmu) == 9769 and len({r['attempt_id'] for r in cmu}) == len(cmu)
assert len(slots) == 3980
assert len({(r['model'], r['domain'], r['task_id'], r['pass']) for r in slots}) == len(slots)
search_ids = {r['attempt_id'] for r in cmu if r['benchmark'] == 'search'}
assert {r['observed_attempt_id'] for r in slots if r['observed_attempt_id'] is not None} == search_ids
assert sum(r['observed_attempt_id'] is None for r in slots) == 1
for bench, expected in cmu_result['benchmark'].items():
    retained = [r for r in cmu if r['benchmark'] == bench and r['retention'] == 'retained']
    assert len(retained) == expected['retained']
    assert abs(sum(r['native_score'] for r in retained) - expected['retained_reward_sum']) < 1e-8
    for state, field in [('removed_truncated', 'round2_truncated'), ('removed_incomplete', 'round3_incomplete')]:
        assert sum(r['benchmark'] == bench and r['retention'] == state for r in cmu) == expected[field]
    assert sum(r['benchmark'] == bench for r in cmu) + expected['round1_unreleased'] == expected['original_attempts']
for r in cmu:
    assert math.isfinite(r['native_score']) and r['score_scale'][0] <= r['native_score'] <= r['score_scale'][1]
unreleased = json.loads((ROOT / 'run_accounting/cmu_unreleased_counts.json').read_text())
assert sum(unreleased['round1_by_benchmark'].values()) == 329
groups = defaultdict(list)
for r in cmu:
    if r['benchmark'] == 'search':
        groups[(r['model'], r['domain'], r['task_id'])].append(r)
assert len(groups) == 995
all_success = complete_success = complete_count = 0
by_model = []
for model in sorted({key[0] for key in groups}):
    model_groups = [rows for key, rows in groups.items() if key[0] == model]
    retained = [r for rows in model_groups for r in rows if r['retention'] == 'retained']
    successes = sum(r['native_score'] for r in retained)
    complete = [rows for rows in model_groups if sum(r['retention'] == 'retained' for r in rows) == 4]
    def oracle(rows):
        return any(r['retention'] == 'retained' and r['native_score'] == 1 for r in rows)
    best_all = sum(oracle(rows) for rows in model_groups)
    best_complete = sum(oracle(rows) for rows in complete)
    all_success += best_all; complete_success += best_complete; complete_count += len(complete)
    by_model.append({'model':model,'scheduled_slots':4*len(model_groups),'retained':len(retained),
        'successes':successes,'retention_rate':len(retained)/(4*len(model_groups)),
        'retained_success_rate':successes/len(retained),'attempt_zero_success_rate':successes/(4*len(model_groups)),
        'complete_groups':len(complete),'complete_group_successes':best_complete,
        'all_groups':len(model_groups),'all_group_successes':best_all})
assert (complete_count,complete_success,all_success) == (722,263,295)
browse = [r for r in cmu if r['benchmark']=='search' and r['domain']=='browsecomp' and r['model']=='DeepSeek-V3.2']
assert len(browse)==496 and sum(r['retention']=='retained' for r in browse)==160
assert sum(r['native_score'] for r in browse if r['retention']=='retained')==69
policies = {'search_models':by_model,'search_group_composition':{
    'complete':{'groups':722,'oracle_successes':263},
    'incomplete':{'groups':273,'oracle_successes':32}},'benchmark_native_policy':{}}
for bench, d in cmu_result['benchmark'].items():
    policies['benchmark_native_policy'][bench] = {
        'zero_exclusions_mean':d['retained_reward_sum']/d['original_attempts'],
        'preserve_released_scores_mean':(d['retained_reward_sum']+d['positive_removed_reward_sum'])/d['original_attempts'],
        'note':'Both assign zero to aggregate-only unreleased exclusions; saved scores do not establish verified final task achievement.'}
assert sum(r['retention'] != 'retained' and r['native_score'] > 0 for r in cmu) == 61
assert len(wild) == 720 and len({(r['model'], r['task_id']) for r in wild}) == len(wild)
all_scored = [r for r in wild if r['score_available'] is True]
cohort_models={'Claude Fable 5','Kimi K3','GLM 5.2'}
scored = [r for r in all_scored if r['model'] == wild_result['selected_model']]
assert len(scored) == 60
assert all(r['native_score'] is None and r['execution_status'] is None and r['score_available'] is None
           for r in wild if r['score_available'] is not True)
expected = wild_result['selected_model_summary']
for field, subset in [
    ('all_mean_score', scored),
    ('assistant_ending_mean_score', [r for r in scored if r['last_original_role'] == 'assistant']),
    ('clean_execution_mean_score', [r for r in scored if r['execution_status'] == 'completed']),
]:
    assert abs(sum(r['native_score'] for r in subset) / len(subset) - expected[field]) < 1e-12
assert sum((r['last_original_role'] == 'assistant') != (r['execution_status'] == 'completed') for r in scored) == 9
assert Counter((r['last_original_role'],r['execution_status']) for r in scored) == {('assistant','completed'):51,('assistant','error'):4,('toolResult','completed'):5}
assert all(math.isfinite(r['native_score']) and 0 <= r['native_score'] <= 1 for r in scored)
errors = [r for r in scored if r['execution_status'] == 'error']
assert len(errors) == 4 and sum(r['native_score'] > 0 for r in errors) == 2
error_zero_mean = sum(r['native_score'] for r in scored if r['execution_status'] != 'error') / len(scored)
assert abs(error_zero_mean - 0.6081933333333334) < 1e-12
policies['wildclaw_error_policy'] = {
    'all_tasks':len(scored),'explicit_errors':len(errors),'positive_score_errors':2,
    'native_mean':sum(r['native_score'] for r in scored)/len(scored),
    'error_zero_mean':error_zero_mean,
    'drop_errors_mean':expected['clean_execution_mean_score'],
}
domains=[]
for model in sorted({r['model'] for r in slots}):
    for domain in sorted({r['domain'] for r in slots}):
        subset=[r for r in cmu if r['benchmark']=='search' and r['source_revision'] and r['model']==model and r['domain']==domain]
        kept=[r for r in subset if r['retention']=='retained']
        n=sum(r['model']==model and r['domain']==domain for r in slots)
        success=sum(r['native_score'] for r in kept)
        domains.append({'model':model,'domain':domain,'scheduled_slots':n,'retained':len(kept),'successes':success,'retained_rate':success/len(kept) if kept else None,'attempt_zero_rate':success/n})
assert len(domains)==15
policies['search_domains']=domains
policies['search_gap_decomposition']={}
for model in sorted({r['model'] for r in domains}):
    cells=[r for r in domains if r['model']==model]
    n=sum(r['scheduled_slots'] for r in cells); c=sum(r['retained'] for r in cells)
    within=sum(r['scheduled_slots']/n*(r['retained_rate']-r['attempt_zero_rate']) for r in cells)
    composition=sum((r['retained']/c-r['scheduled_slots']/n)*r['retained_rate'] for r in cells)
    global_gap=sum(r['successes'] for r in cells)/c-sum(r['successes'] for r in cells)/n
    assert abs(within+composition-global_gap)<1e-12
    policies['search_gap_decomposition'][model]={'total_gap':global_gap,'within_domain_retention':within,'domain_composition':composition}

(ROOT/'policy_comparison.json').write_text(json.dumps(policies,indent=2,sort_keys=True)+'\n')
print('Verified: 9,769 CMU attempts, 3,980 search slots, 720 WildClawBench pairs; native-score preservation and aggregate reconciliation passed.')

if (ROOT/'extension_results.json').exists():
    import pyarrow.parquet as pq
    extension=json.loads((ROOT/'extension_results.json').read_text())
    status_scored=[r for r in all_scored if r['model'] in cohort_models]
    assert len(status_scored)==len(extension['runs'])==180
    assert len(all_scored)==(720 if (ROOT/'full_roster_results.json').exists() else 300)
    originals=pq.read_table(ROOT/'independent_data/wildclaw/train.parquet').to_pylist()
    exported={(r['model'],r['task_id']):r for r in wild}
    assert len(originals)==len(exported)==720
    nonassistant=0
    for row in originals:
        terminal=json.loads(row['trajectory'])[-1]
        record=exported[(row['model_name'],row['task_id'])]
        assert record['last_original_role']==terminal['role']
        assert record.get('native_stop_reason')==terminal.get('stopReason')
        assert ('native_stop_reason' in record) == ('stopReason' in terminal)
        nonassistant += terminal['role']!='assistant'
    assert nonassistant==54
    for source in extension['runs']:
        r=exported[(source['model'],source['task_id'])]
        assert (r['last_original_role'],r.get('native_stop_reason'),r['execution_status'],r['native_score']) == (source['last_role'],source['stop_reason'],source['trace_status'],source['score'])
    assert sum((r['last_original_role']=='assistant')!=(r['execution_status']=='completed') for r in status_scored)==33
    assert sum(r['native_score']>0 and r['last_original_role']=='toolResult' for r in status_scored)==5
    assert sum(r['native_score']>0 and r['execution_status']!='completed' for r in status_scored)==5
    assert sum(r['execution_status']=='completed' and r.get('native_stop_reason') in ('aborted','length') for r in status_scored)==10
    slugs={'Claude Fable 5':'claude_fable5','Kimi K3':'kimi_k3','GLM 5.2':'glm52'}
    for r in status_scored:
        path=ROOT/'independent_data/wildclaw/sessions'/slugs[r['model']]/(r['task_id']+'.jsonl')
        with path.open() as handle: header=json.loads(handle.readline())
        assert header['task_id']==r['task_id'] and header['trace_status']==r['execution_status']
    print('Verified source terminal events for all 720 pairs and native session joins/grade accounting for 180 runs.')

zip_results=json.loads((ROOT/'zip_score_results.json').read_text())
assert len(zip_results['runs'])==120
for source in zip_results['runs']:
    record=exported[(source['model'],source['task_id'])]
    assert record['native_score']==source['score'] and record['execution_status'] is None
    assert record['last_original_role']==source['last_role'] and record.get('native_stop_reason')==source['stop_reason']
assert sum(r['score_available'] is None for r in wild)==(0 if (ROOT/'full_roster_results.json').exists() else 420)
print('Verified ZIP extension: 120 recorded grades, unknown exporter status; historical staged score coverage 300/720; final coverage is checked below.')

if (ROOT/'full_roster_results.json').exists():
    full=json.loads((ROOT/'full_roster_results.json').read_text())
    assert len(full['runs'])==720
    assert len({(r['model'],r['task_id']) for r in full['runs']})==720
    for source in full['runs']:
        record=exported[(source['model'],source['task_id'])]
        assert record['native_score']==source['score'] and record['execution_status']==source['trace_status']
        assert record['last_original_role']==source['last_role'] and record.get('native_stop_reason')==source['stop_reason']
    assert sum(r['execution_status'] is not None for r in wild)==600
    for directory in (ROOT/'independent_data/wildclaw/sessions').iterdir():
        for path in directory.glob('*.jsonl'):
            with path.open() as handle: header=json.loads(handle.readline())
            # Directory slug is paired to model by the full-roster adapter.
            candidates=[r for r in full['runs'] if r['task_id']==header['task_id'] and r['model'] in full['models'] and full['models'][r['model']].get('session_slug')==directory.name]
            assert len(candidates)==1
            assert candidates[0]['trace_status']==header['trace_status']
    print('Verified full roster: 720 recorded grades, 600 native session joins, 120 unknown exporter statuses.')
