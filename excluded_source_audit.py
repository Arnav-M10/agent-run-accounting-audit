#!/usr/bin/env python3
"""Independent metadata consistency audit. Never imports corpus adapters.

Records are selected by sorted original source identity with a fixed RNG seed.
Reward stratification is a deliberate targeted source consistency audit, not
an outcome blind sample and not an estimate of error prevalence. The exact
whole source counts are structural counts, not full semantic validation.
No message content or evaluation trace text is included in output.
"""
import argparse
import collections
import hashlib
import json
import random
from pathlib import Path

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cmu-data', type=Path, default=Path('data'))
    ap.add_argument('--ledger', type=Path, default=Path('run_accounting/cmu_attempts.jsonl'))
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--seed', type=int, default=20261007)
    ap.add_argument('--declare-only', action='store_true')
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    paths = {
        'removed_incomplete': args.cmu_data / 'removed_incomplete.json',
        'removed_truncated': args.cmu_data / 'removed_truncated.json',
        'ledger': args.ledger,
    }
    src = {k: json.loads(p.read_text()) for k, p in paths.items() if k != 'ledger'}
    incomplete = src['removed_incomplete']
    errors = [r for r in src['removed_truncated'] if (r.get('eval_details') or {}).get('status') == 'error']
    strata = [
        ('no_final_answer', incomplete, 10),
        ('error_zero_reward', [r for r in errors if r['reward'] == 0], 10),
        ('error_positive_mcp', [r for r in errors if r['reward'] > 0 and r['benchmark'] == 'mcpbench'], 5),
        ('error_positive_swe', [r for r in errors if r['reward'] > 0 and r['benchmark'] == 'swebench'], 5),
    ]
    rng = random.Random(args.seed)
    chosen = []
    declaration = {'seed': args.seed, 'algorithm': 'Python random.Random(seed); successive random.sample on original source IDs sorted lexicographically; selected IDs sorted within each stratum',
                   'purpose': 'Targeted source consistency by recorded reward; not outcome blind or prevalence representative',
                   'scope': '30 excluded records; exact source counts; no full semantic validation; native recorded grade only, not grade achievement',
                   'source_sha256': {k: sha(p) for k,p in paths.items()}, 'strata': []}
    for name, records, n in strata:
        ordered = sorted(records, key=lambda r: r['id'])
        sample = sorted(rng.sample(ordered, min(n,len(ordered))), key=lambda r: r['id'])
        chosen.extend((name,r) for r in sample)
        declaration['strata'].append({'name': name, 'population': len(ordered), 'requested': n, 'selected': len(sample), 'source_ids': [r['id'] for r in sample]})
    manifest = args.output / 'selection_declaration.json'
    if args.declare_only:
        save(manifest, declaration)
        print(json.dumps({'declaration': str(manifest), 'sha256': sha(manifest), 'selected': len(chosen)}))
        return
    if not manifest.exists() or json.loads(manifest.read_text()) != declaration:
        raise SystemExit('Selection declaration absent or differs; run --declare-only BEFORE individual checks.')
    # Only after verifying the previously written declaration do individual comparisons begin.
    ledger = [json.loads(line) for line in paths['ledger'].read_text().splitlines() if line.strip()]
    index = collections.defaultdict(list)
    for row in ledger:
        index[row['attempt_id']].append(row)
    comparison_map = {'id':'attempt_id', 'benchmark':'benchmark', 'source_model':'model', 'domain':'domain', 'task_id':'task_id', 'pass':'pass', 'reward':'native_score'}
    rows = []
    mismatches = []
    for stratum,r in chosen:
        matches = index[r['id']]
        expected_retention = 'removed_incomplete' if stratum == 'no_final_answer' else 'removed_truncated'
        source_metadata = {k:r.get(k) for k in comparison_map}
        source_metadata.update({'removal_reason':r.get('removal_reason'), 'last_original_role':r['messages'][-1].get('role') if r.get('messages') else None,
                                'eval_status':(r.get('eval_details') or {}).get('status')})
        discrepancies = []
        if len(matches) != 1:
            discrepancies.append({'field':'identity_match_count','source':1,'ledger':len(matches)})
        else:
            l = matches[0]
            for sk,lk in comparison_map.items():
                if sk not in r or lk not in l or r[sk] != l[lk]:
                    discrepancies.append({'field':lk,'source':r.get(sk),'ledger':l.get(lk)})
            for field,expected in [('retention',expected_retention), ('last_original_role',source_metadata['last_original_role']), ('score_available',r.get('reward') is not None)]:
                if l.get(field) != expected:
                    discrepancies.append({'field':field,'source':expected,'ledger':l.get(field)})
        result = {'stratum':stratum,'source_metadata':source_metadata,'ledger_metadata':matches[0] if len(matches)==1 else None,'discrepancies':discrepancies}
        rows.append(result)
        if discrepancies:
            mismatches.append(result)
    counts = {'incomplete_total':len(incomplete), 'incomplete_reasons':dict(collections.Counter(r['removal_reason'] for r in incomplete)),
              'truncated_total':len(src['removed_truncated']), 'truncated_error_status':len(errors),
              'error_positive_total':sum(r['reward']>0 for r in errors),
              'error_positive_benchmark':dict(collections.Counter(r['benchmark'] for r in errors if r['reward']>0))}
    report = {'declaration':declaration,'declaration_sha256':sha(manifest),'source_counts':counts,'sample_size':len(rows),'mismatch_count':len(mismatches),
              'checked_fields':list(comparison_map.values())+['retention','last_original_role','score_available'],
              'unavailable_comparisons':{'exclusion_reason':'Ledger has retention category but no original removal_reason field; original reason preserved in metadata only.',
                                          'error_status':'Ledger execution_status and failure_attribution are null for these records; no original error flag field is retained. Source eval_details.status is metadata only.'},
              'source_schema_fields':{name:sorted(set(k for r in records for k in r)) for name,records in src.items()},
              'ledger_schema_fields':sorted(set(k for r in ledger for k in r)),
              'records':rows}
    output = args.output / 'excluded_source_audit.json'
    save(output,report)
    print(json.dumps({'report':str(output),'report_sha256':sha(output),'script_sha256':sha(Path(__file__)),'sample_size':len(rows),'mismatch_count':len(mismatches),'source_counts':counts},sort_keys=True))
    if mismatches:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
