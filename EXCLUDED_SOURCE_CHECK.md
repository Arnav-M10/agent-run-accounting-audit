# Targeted excluded-record source consistency

A separate agent reconstructed source metadata directly from the original excluded JSON records without calling corpus adapters. This extends the earlier retained-record spot check to the exclusions central to the audit. It is agent-assisted source consistency evidence, not a human replication or independent task-achievement grading.

Before individual comparisons, seed 20261007 selected from source IDs sorted lexically: 10 no-final-answer records from 888, 10 error-marked zero-reward records from 167, 5 positive MCP records from 55, and 5 positive SWE records from 6. Recorded reward defines these deliberate strata. This is not an outcome-blind sample or an estimate of error prevalence. The declaration is preserved in excluded_source_check/selection_declaration.json.

All 30 records matched the checked ledger fields: identity, benchmark, model, domain, task, pass, recorded grade, retention category, last original role and score availability. Source counts independently confirm 888 no-final-answer exclusions (597 tool-ending, 291 user-ending), 228 error-marked truncations, and 61 positive saved rewards (55 MCP, 6 SWE). No final message or error label independently establishes task achievement.

The ledger does not retain original removal_reason or original error-status flags; execution_status and failure_attribution are null. Those are explicitly unavailable comparisons. Original metadata is preserved in the report without filling these fields or embedding message contents. Aggregate first-round exclusions remain outside this identifiable sample.

Run after the pinned raw acquisition, from the artifact directory:

```sh
python3 excluded_source_audit.py --output excluded_source_check --declare-only
python3 excluded_source_audit.py --output excluded_source_check
```

Use --cmu-data and --ledger for other input locations. The second command requires an identical previously saved declaration. Source data are read only. The implementation exits unsuccessfully on mismatches and exports only metadata; no inference API is called. CLI paths were adapted for artifact reuse and replayed without changing selected records or findings.
