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

## What these cases establish

CMU supplies total attempt counts but lacks identifiers for its earliest 329 exclusions. Its all-attempt summaries therefore use aggregate counts; only independently identifiable grids support more detailed reconstruction. WildClawBench supplies all 720 released model–task pairs. The three selected models supply 180 scores and execution-status records, allowing the final-role/status cross-tabulation. Neither release establishes the absence of unpublished retries or failures.

These checks use released records and local computation. They require no new model inference or paid API calls.

## Implemented exports

The audit scripts write `run_accounting/cmu_attempts.jsonl` (9,769 released attempts), `cmu_search_slots.jsonl` (3,980 scheduled search slots), `cmu_unreleased_counts.json` (329 aggregate-only exclusions), and `wildclaw_released_pairs.jsonl` (720 released pairs). The WildClawBench export has examined scores/statuses for 180 pairs; the other 540 retain null availability, score, and status. CMU execution status and retry history remain unknown in these exports. Cleaning disposition is recorded separately and is not converted into native execution status.

The search slot with no released record has a null attempt ID and an aggregate-only coverage label; it is not labeled as an uninitiated attempt. `verify_accounting.py` checks ledger reconciliation and reproduces the three selected models' alternative score means from the exports.

The later three-model extension replaces the WildClawBench ledger with 180 examined grades/statuses and 540 unexamined pairs. The original one-model script retains its initial outputs for reproducibility; run extension_audit.py before final verification. Stop reasons are recorded for all released pairs directly from their terminal events. The verifier reads all 720 source terminal events and all 180 examined native session headers, in addition to consistency checks against generated summaries.
