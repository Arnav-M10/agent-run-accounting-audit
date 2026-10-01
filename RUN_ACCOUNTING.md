# Run-accounting protocol

This proposed protocol accompanies the two-case audit. It separates collection coverage, execution termination, and task outcome. It is a reporting proposal, not a validated standard.

## Record each scheduled slot and observed attempt

Use a slot ledger for the intended evaluation grid and an attempt ledger for actual executions. A slot can have zero, one, or multiple attempts; retries must not silently overwrite earlier attempts. Do not reconstruct an unreleased attempt identifier from aggregate counts.

| Field | Meaning |
|---|---|
| `slot_id` | Stable identifier for benchmark, task, model/configuration, and scheduled pass. |
| `attempt_id` | Unique observed execution identifier; absent slots have no attempt ID. |
| `retry_of` | Prior attempt ID, if recorded. Unknown retry history remains unknown. |
| `source_revision` | Dataset or evaluation version identifying the evidence. |
| `retention` | Retained, excluded, or unknown, with the source's reason recorded separately. |
| `last_original_role` | Last original event role, or null for an unavailable/empty trace. Exported warnings are excluded from this measurement. |
| `native_stop_reason` | Stop reason on the final original event, if present; null is distinct from a normal stop. |
| `execution_status` | Native status plus its documented meaning. Use unknown when not recorded; do not infer clean execution from the final role. |
| `score_available` | Whether a native task score is recorded in the audited evidence. Use null when the source has not been examined; this does not mean that no score exists elsewhere. |
| `native_score` | Recorded score, with its scale and grading version; null when unavailable. Zero and unavailable are different values. |
| `failure_attribution` | Source-supported cause and evidence reference; unknown when attribution is unresolved. |

Include an explicit coverage note when only aggregate exclusion counts are available. Preserve those counts as aggregate evidence rather than inventing rows or attributing them to models.

## Declare every aggregate's inclusion policy

For each reported mean, publish the population, numerator, denominator, score scale, missing-score rule, retry rule, and execution-status rule. Keep native scores available even when a separate operational metric assigns errors zero.

- **Native-score mean:** sum of available native scores divided by the number of scored attempts. Report score coverage against all observed attempts and scheduled slots.
- **Conditional mean:** the same calculation after a stated inclusion rule, such as retained traces or assistant-ending traces. Report how many rows the rule removes and their score availability.
- **Operational mean:** define which attempts or scheduled slots constitute the population and explicitly state any zero assignment. An absent scheduled slot is not evidence that an attempt was initiated.
- **Repeated-pass success:** state the number of planned passes, how missing passes are handled, whether retries count as passes, and how many model–task groups are included. Groups with all passes retained and all scheduled groups are different populations.

When causes are supported, report agent, endpoint/harness, and unresolved failures separately. Cause separation does not by itself specify a denominator; state whether each category remains in the performance population.

## Reconciliation checks

1. Verify unique slot and attempt IDs and valid references between the ledgers.
2. Reconcile scheduled slots into slots with and without observed attempts. Report extra/retry attempts separately.
3. Reconcile observed attempts into retained, excluded, and unknown dispositions.
4. Reconcile scored and unscored attempts. Check score bounds without replacing missing values with zero.
5. Cross-tabulate final role against explicit execution status and score availability. Report disagreement rather than treating either field as task success.
6. Reproduce released aggregate scores before calculating alternative inclusion policies. Explain any mismatch.

## Current coverage and implemented exports

Final WildClawBench coverage: all 720 recorded grades and terminal events; 600 exporter-status headers, 120 unknown statuses. The source manifest covers 624 inputs.

CMU supplies 9,769 released attempt rows plus 329 aggregate-only earliest exclusions with no released IDs. Search supplies a reconstructed 3,980-slot grid with one aggregate-only coverage slot. Retry histories remain unknown.

The pipeline writes run_accounting/cmu_attempts.jsonl, cmu_search_slots.jsonl, cmu_unreleased_counts.json, and wildclaw_released_pairs.jsonl. Cleaning disposition remains separate from native execution status. Unknown coverage is never converted to zero or a fabricated attempt ID.

Historical stages: independent_audit.py records the original 60-grade case; extension_audit.py records three models/180 grades and statuses; zip_score_audit.py adds 120 grades with unknown exporter status. The original archive-selection wording is preserved with a dated correction in EXTENSION_PLAN.json. ZIP_EXTENSION_PLAN.json records the subsequent addition before ZIP outcomes were read. FULL_ROSTER_PLAN.json records completion of the released roster after that stage.

terminal_measurement_audit.py reads native event metadata for every released pair. check_ledger.py provides reusable consistency checks with explicit identity fields and preserves absent versus null values. Corpus-specific adapters perform extraction; verify_accounting.py checks pinned sources and reconciliation. No independent artifact regrading or paid inference is performed.

## Worked analysis example

An analyst who averages only Claude Fable 5 assistant-ending traces reports 67.64% over 55 runs instead of the released native mean 62.00% over 60. The pair ledger exposes last_original_role and native_score for the five omitted tool-ending runs, while score_available distinguishes a missing grade from zero. To report the source's scored population, keep all 60 recorded grades; to study assistant-ending traces, report the conditional population explicitly. This does not prove either is the right metric for every question.

For a new corpus using these field names:

```sh
python check_ledger.py my_pairs.jsonl --identity model,task_id
```

The result reports valid, rows, numeric_scores, issue counts, and category cross-tabs. A passing check establishes metadata consistency, not source truth or task achievement. Use extraction and source verification appropriate to that corpus.
