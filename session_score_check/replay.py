"""Source replay; reads pinned Parquet, emits only aggregate facts, no spans.
Requires pyarrow. No inference API calls. Public metadata/card lack a license declaration;
source files are not included in this package.
"""
import argparse,collections,hashlib,json,pathlib
import pyarrow.parquet as pq
p=argparse.ArgumentParser();p.add_argument('--root',required=True);args=p.parse_args();root=pathlib.Path(args.root)
manifest=json.loads((pathlib.Path(__file__).parent/'source_shards.json').read_text());rows=[]
for entry in manifest:
 src=root/entry['file'];assert src.stat().st_size==entry['size'];assert hashlib.sha256(src.read_bytes()).hexdigest()==entry['sha256']
 rows.extend(pq.read_table(src,columns=['run_id','session_id','config_path','harness','benchmark','models','score','success','status']).to_pylist())
assert len(rows)==10056 and len({r['session_id'] for r in rows})==10056
for run in ['8169c7b3047e','7c39d2802396','b208193b3ce4']:
 r=[x for x in rows if x['run_id']==run];assert len(r)==100 and len({x['session_id'] for x in r})==100
 assert all(x['score'] in [0.0,1.0] for x in r)
 # This is the reviewed source's outcome-status-to-completed mapping; it is
 # not an independently proven data-generating version or archived execution index.
 eligible=[x for x in r if x['status'] not in ['error','cancelled','unknown']]
 excluded=[x for x in r if x['status'] in ['error','cancelled','unknown']]
 assert all(x['score']==0 for x in excluded)
 print(json.dumps({'run_id':run,'session_count':len(r),'numeric_grade_count':len(r),'grade_sum':sum(x['score'] for x in r),'eligible_count':len(eligible),'eligible_grade_sum':sum(x['score'] for x in eligible),'all_mean':sum(x['score'] for x in r)/len(r),'eligible_mean':sum(x['score'] for x in eligible)/len(eligible),'status_counts':dict(collections.Counter(x['status'] for x in r))},sort_keys=True))
