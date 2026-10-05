"""Audit every score archive in the pinned released roster; no new inference."""
from pathlib import Path
import json, tarfile, hashlib
from collections import Counter
import pyarrow.parquet as pq
root=Path(__file__).resolve().parent; data=root/'independent_data/wildclaw'
rows=pq.read_table(data/'train.parquet').to_pylist()
cohorts=[('Claude Fable 5','claude_fable5'),('Claude Opus 4.8 Thinking','claude_opus_4_8_thinking'),('GLM 5.2','glm52'),('GPT-5.6 Sol','gpt56_sol'),('Grok 4.5','grok45'),('Hy3','hy3'),('Intern-S2-Preview-397B','intern-s2-preview-397b'),('Kimi K2.7 Code','kimi_k2.7_code'),('Kimi K3','kimi_k3'),('Muse Spark 1.1','muse_spark_1_1')]
result={'revision':'d2816016a7a7b41fa6b7ba368b28ddafcb54fd93','selection_rule':'Full pinned released roster: all 12 models, 720 grades, exporter headers for 10 models/600 runs. Staged acquisition, not a general agent population sample.','models':{},'runs':[]}
for model,slug in cohorts:
    source=[r for r in rows if r['model_name']==model]
    scores={}; published=[]
    with tarfile.open(data/('output_'+slug+'.tar.gz')) as archive:
        for member in archive:
            if not member.isfile():continue
            if member.name.endswith('/score.json'):
                matches=set(member.name.split('/')) & {r['task_id'] for r in source}
                assert len(matches)==1,member.name
                task=matches.pop()
                assert task not in scores
                scores[task]=json.load(archive.extractfile(member))['overall_score']
            elif '/summary_all' in member.name and member.name.endswith('.json'):
                obj=json.load(archive.extractfile(member))
                if 'global_avg' in obj: published.append(obj['global_avg'])
    headers={}
    for path in (data/'sessions'/slug).glob('*.jsonl'):
        with path.open() as handle: h=json.loads(handle.readline())
        assert h['task_id'] not in headers
        headers[h['task_id']]=h
    assert set(scores)==set(headers)=={r['task_id'] for r in source} and len(scores)==60
    records=[]
    for row in source:
        task=row['task_id']; messages=json.loads(row['trajectory']); score=scores[task]
        assert 0<=score<=1
        assert headers[task]['trace_status'] in ('completed','error','interrupted')
        records.append({'model':model,'task_id':task,'last_role':messages[-1]['role'],
                        'stop_reason':messages[-1].get('stopReason'),'trace_status':headers[task]['trace_status'],
                        'score':score,'recorded_status_source':'session export header'})
    def mean(items):return sum(r['score'] for r in items)/len(items) if items else None
    all_mean=mean(records); assert any(abs(all_mean-p)<1e-8 for p in published),(model,published,all_mean)
    assistant=[r for r in records if r['last_role']=='assistant']; completed=[r for r in records if r['trace_status']=='completed']
    errors=[r for r in records if r['trace_status']=='error']
    native_stop=[r for r in records if r['stop_reason']=='stop']
    result['models'][model]={'session_slug':slug,'all_runs':60,'native_mean':all_mean,'assistant_runs':len(assistant),'assistant_mean':mean(assistant),
      'native_stop_runs':len(native_stop),'native_stop_mean':mean(native_stop),'export_completed_runs':len(completed),'export_completed_mean':mean(completed),
      'noncompleted_zero_mean':sum(r['score'] for r in records if r['trace_status']=='completed')/60,
      'positive_noncompleted_runs':sum(r['score']>0 and r['trace_status']!='completed' for r in records),
      'positive_tool_ending_runs':sum(r['score']>0 and r['last_role']=='toolResult' for r in records),
      'error_zero_mean':sum(r['score'] for r in records if r['trace_status']!='error')/60,
      'status_counts':dict(Counter(r['trace_status'] for r in records)),
      'role_status_counts':dict(Counter(r['last_role']+'/'+r['trace_status'] for r in records)),
      'status_stop_counts':dict(Counter(r['trace_status']+'/'+str(r['stop_reason']) for r in records)),
      'role_status_disagreement':sum((r['last_role']=='assistant') != (r['trace_status']=='completed') for r in records),
      'positive_error_runs':sum(r['score']>0 for r in errors),
      'completed_aborted_or_length':sum(r['trace_status']=='completed' and r['stop_reason'] in ('aborted','length') for r in records),
    }
    result['runs'].extend(records)
zip_results=json.loads((root/'zip_score_results.json').read_text())
for model,summary in zip_results['models'].items():
    model_runs=[r for r in zip_results['runs'] if r['model']==model]
    stopped=[r for r in model_runs if r['stop_reason']=='stop']
    summary['native_stop_runs']=len(stopped)
    summary['native_stop_mean']=sum(r['score'] for r in stopped)/len(stopped) if stopped else None
    result['models'][model]=summary
result['runs'].extend(zip_results['runs'])
assert len(result['runs'])==720
assert len(result['models'])==12
(root/'full_roster_results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result['models'],indent=2))

# Export all released pairs; examined grades/statuses come from the three cohorts.
scored={(r['model'],r['task_id']):r for r in result['runs']}
ledger=root/'run_accounting'; ledger.mkdir(exist_ok=True)
with (ledger/'wildclaw_released_pairs.jsonl').open('w') as handle:
    for row in rows:
        r=scored.get((row['model_name'],row['task_id']))
        terminal=json.loads(row['trajectory'])[-1]
        entry={
          'model':row['model_name'],'task_id':row['task_id'],'retention':'released',
          'last_original_role':terminal['role'],
          'execution_status':r['trace_status'] if r else None,'score_available':True if r else None,
          'native_score':r['score'] if r else None,'score_scale':[0,1],'retry_of':None,'failure_attribution':None,
          'source_revision':result['revision']}
        if 'stopReason' in terminal:
            entry['native_stop_reason'] = terminal['stopReason']
        handle.write(json.dumps(entry,sort_keys=True)+'\n')
