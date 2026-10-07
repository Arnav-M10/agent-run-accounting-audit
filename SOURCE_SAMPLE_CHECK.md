# Fixed source-to-ledger spot check

A separate implementation reconstructed fields directly from local raw inputs, without calling the corpus adapters. Seed 20261007 selected five retained records from each of the six CMU benchmarks and five WildClaw model-task pairs (three TAR, two ZIP), from sorted source identity frames before inspecting sampled outcomes. All 35 matched the packaged fields checked. The report preserves selected identities, source/member hashes, checked fields and mismatches.

CMU fields: identity, benchmark/model/domain/task/pass, native reward, retained label, score availability and final original role. CMU exporter status remains unknown, rather than borrowing heterogeneous benchmark status labels. WildClaw fields: identity, native archive grade, final original role, native stop value and field presence, plus exporter header status for TAR records. ZIP exporter status remains unavailable. No sampled CMU final event contains stopReason; the checker records this rather than inferring it.

This is exact source consistency for a fixed retained-record sample. It does not establish full pipeline correctness, excluded-record extraction, semantic grader validity, hidden retries, independent human adoption or an external reviewer validation. The implementation was prepared by a separate reviewing agent; it is not a human replication. Hashes identify the inputs; hashing alone does not validate extraction.

After acquiring the pinned inputs listed in README.md, run from the artifact directory with the existing PyArrow requirement:

```sh
python3 source_sample_audit.py --cmu-data data \
  --wildclaw-data independent_data/wildclaw \
  --ledger-root run_accounting --output source_sample_report.json
```

The code uses no model inference and reads sources without executing trace contents. It exits unsuccessfully on a field mismatch. The supplied source_sample_report.json has 30 CMU retained records, 5 WildClaw pairs, and zero mismatches. It contains metadata and hashes, not raw trajectories or task outputs.
