"""Read both previously omitted ZIP score archives; exporter status remains unknown."""
from pathlib import Path
import json,zipfile,hashlib
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'independent_data/wildclaw'
rows=pq.read_table(DATA/'train.parquet').to_pylist()
result={'revision':'d2816016a7a7b41fa6b7ba368b28ddafcb54fd93','plan':'ZIP_EXTENSION_PLAN.json','status_coverage':'No exported session directories at pinned revision for either ZIP model; no status inferred.','models':{},'runs':[]}
for model,file in [('Qwen3.8 Max','output_qwen3.8-max.zip'),('Qwen3.8-27B (vLLM)','output_qwen3.8-27b-vllm.zip')]:
    scores={};published=[]
    with zipfile.ZipFile(DATA/file) as archive:
        for name in archive.namelist():
            if name.endswith('/score.json'):
                task=name.split('/')[3]
                assert task not in scores
                scores[task]=json.loads(archive.read(name))['overall_score']
            elif '/summary_all' in name and name.endswith('.json'):
                obj=json.loads(archive.read(name))
                if 'global_avg' in obj:published.append(obj['global_avg'])
    source=[r for r in rows if r['model_name']==model]
    assert set(scores)=={r['task_id'] for r in source} and len(scores)==60
    records=[]
    for row in source:
        event=json.loads(row['trajectory'])[-1];score=scores[row['task_id']]
        assert 0<=score<=1
        records.append({'model':model,'task_id':row['task_id'],'last_role':event['role'],'stop_reason':event.get('stopReason'),'score':score,'trace_status':None})
    def mean(x):return sum(r['score'] for r in x)/len(x) if x else None
    native=mean(records);assert any(abs(native-p)<1e-8 for p in published),(model,native,published)
    assistant=[r for r in records if r['last_role']=='assistant']
    result['models'][model]={'all_runs':60,'native_mean':native,'assistant_runs':len(assistant),'assistant_mean':mean(assistant),'positive_nonassistant_runs':sum(r['score']>0 and r['last_role']!='assistant' for r in records),'export_status_examined_runs':0,'source_archive':file,'sha256':hashlib.sha256((DATA/file).read_bytes()).hexdigest()}
    result['runs'].extend(records)
(ROOT/'zip_score_results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
ledger=ROOT/'run_accounting/wildclaw_released_pairs.jsonl'
scored={(r['model'],r['task_id']):r for r in result['runs']}
entries=[json.loads(line) for line in ledger.read_text().splitlines()]
for entry in entries:
    run=scored.get((entry['model'],entry['task_id']))
    if run:
        entry['score_available']=True;entry['native_score']=run['score'];entry['execution_status']=None
ledger.write_text(''.join(json.dumps(e,sort_keys=True)+'\n' for e in entries))
print(json.dumps(result['models'],indent=2))
