#!/usr/bin/env python3
"""Convert pinned parquet to complete aggregate JSON; requires existing PyArrow."""
import argparse,hashlib,json
from pathlib import Path
import pyarrow.parquet as pq
from replay import validate

p=argparse.ArgumentParser();p.add_argument('--parquet',required=True);p.add_argument('--output',required=True);p.add_argument('--manifest',default=str(Path(__file__).with_name('source_manifest.json')));a=p.parse_args()
manifest=json.loads(Path(a.manifest).read_text());src=Path(a.parquet)
if hashlib.sha256(src.read_bytes()).hexdigest()!=manifest['parquet_sha256']:raise ValueError('Parquet does not match pinned SHA256')
rows=pq.read_table(src).to_pylist();validate(rows)
Path(a.output).write_text(json.dumps({'provenance':manifest,'rows':rows},indent=2,sort_keys=True)+'\n')
