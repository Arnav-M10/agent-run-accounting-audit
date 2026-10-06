# Generic ledger summaries

`summarize_ledger.py` uses only Python's standard library and reads JSONL without changing source values. It reports recorded scores, never infers task success from roles or status, and does not infer initiated attempts from scheduled slots. The population is the supplied ledger's records; users must describe their origin.

Run from this directory:

```sh
python3 summarize_ledger.py run_accounting/wildclaw_released_pairs.jsonl --group-by model --missing-grade error
python3 summarize_ledger.py run_accounting/wildclaw_released_pairs.jsonl --group-by model --include 'last_original_role="assistant"' --missing-grade error
python3 summarize_ledger.py run_accounting/wildclaw_released_pairs.jsonl --group-by model --include 'native_stop_reason="stop"' --missing-grade error
python3 summarize_ledger.py run_accounting/wildclaw_released_pairs.jsonl --group-by model --include 'execution_status="completed"' --missing-grade error
python3 demo_summarize_ledger.py > summarize_ledger_example.json
```

Repeat `--group-by` for multiple fields and `--include` for ANDed exact equality rules. Values use JSON syntax: strings need double quotes, and booleans/numbers/null are typed. An equality rule for `null` requires an explicitly present null field; an absent field does not match. Group keys preserve `present: false` separately from `present: true, value: null`. Unknown field names and unsupported operators produce errors. There are no automatic retention rules.

Zero assignment to unknown grades requires a declared group scale containing zero; incompatible or wholly undeclared scales are rejected. The required `--missing-grade` policy applies after inclusion: `error` refuses an unknown grade, `exclude` divides by the scored count, and `zero` divides by the selected population count while assigning unknown grades zero only in the reported policy mean. `recorded_score_mean` always uses recorded scores. `null_score_count` and `absent_score_count` distinguish both unknown cases. The output declares the mean denominator, inclusion rules, score coverage, removed count, scale, and machine-readable `conditional_population`, `uses_scored_denominator`, and `unknown_grades_assigned_zero` labels.

Scores default to `native_score`, with a two-number `score_scale` declaration; override these field names using `--score-field` and `--scale-field`. Every recorded score must be finite, numeric, and within its declared scale. Boolean scores, malformed scales, and mixed scales within any source group are rejected, including records excluded by the selected rule. Unknown scale declarations are counted. The tool does not pool mixed scales automatically.

The read-only demonstration checks 46 means against `full_roster_results.json`: all records, assistant ending, and native `stop` for 12 models, plus exporter completed for the ten models with examined exporter status. The two Qwen models have unexamined exporter status and therefore an empty exporter-completed population, a null mean, and 60 excluded records each. This is absence of examined status evidence, not evidence of unsuccessful execution.

Example for Claude Fable 5 (scores on [0,1]):

| Declared population | Included | Scored | Unknown | Excluded | Mean |
|---|---:|---:|---:|---:|---:|
| All supplied records | 60 | 60 | 0 | 0 | 0.620045 |
| `last_original_role="assistant"` | 55 | 55 | 0 | 5 | 0.676413 |
| `native_stop_reason="stop"` | 48 | 48 | 0 | 12 | 0.728956 |
| `execution_status="completed"` | 56 | 56 | 0 | 4 | 0.651636 |

Full machine-readable output is in `summarize_ledger_example.json`.

The declared score and scale fields must each occur in at least one source record; wholly absent field names are rejected to catch misspelled overrides. For wholly unknown grades or scales, record explicit null values. Per-row absence remains distinct from explicit null when the field exists elsewhere. Numeric equality values must be finite, including exponent notation. CMU transfer commands and denominator limits appear in REPORTER_TRANSFER.md.
