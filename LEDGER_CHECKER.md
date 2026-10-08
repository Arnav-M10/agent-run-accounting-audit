# Reusable metadata-ledger checker

`check_ledger.py` uses only Python's standard library. It accepts arbitrary JSONL
metadata ledgers using the protocol's field names. Give the identity fields
explicitly; a released model/task pair is not automatically an execution ID.

From this directory:

```sh
python check_ledger.py run_accounting/cmu_attempts.jsonl --identity attempt_id
python check_ledger.py run_accounting/cmu_search_slots.jsonl --identity benchmark,domain,model,task_id,pass --reference-ledger run_accounting/cmu_attempts.jsonl
python check_ledger.py run_accounting/wildclaw_released_pairs.jsonl --identity model,task_id
```

Each command prints JSON and exits with 1 for detected issues, otherwise 0.
Redirect stdout to save the report. Optional `--reference-field` and
`--target-field` configure an ID join between a ledger and a reference ledger.
A null reference is reported as unlinked evidence, never as proof that an
attempt was not initiated. Target IDs must be unique.

Checks cover malformed JSON rows, missing or duplicate identities, recorded
score availability contradictions, nonnumeric or nonfinite grades, recorded
grade ranges, and unresolved or ambiguous reference IDs. Reports include issue
counts and up to ten examples. They also count retention, final role, execution
status, native stop reason, coverage, and grade availability, plus their
role/status/availability cross-tabulation.

Category entries retain `present: false` for an absent field and
`present: true, value: null` for an explicit unknown. Zero is a numeric score;
unknown score availability remains null. Grades without score-range evidence
are counted explicitly and are not given an invented scale. No scores are
changed, and no terminal role or status is interpreted as success. This is a
metadata consistency check, not source verification, independent regrading, or
a claim that every scheduled slot has an observed execution. Aggregate-only
exclusions remain outside row counts.

## Demonstration on the supplied ledgers

`ledger_check_results.json` contains the full reports generated from the real
metadata ledgers. All three passed with no duplicate identities, recorded
score-range violations, or availability contradictions:

| Ledger | Rows | Numeric grades | Reference evidence |
|---|---:|---:|---|
| CMU attempts | 9,769 | 9,769 | Not requested |
| CMU search slots | 3,980 | 0 | 3,979 linked IDs; one explicit null |
| WildClawBench pairs | 720 | 720 | Not requested |

All recorded numeric grades had declared ranges. CMU execution status is null
on all 9,769 rows. WildClawBench score availability is true for all 720 pairs; exporter status remains
null for 120 pairs. The slot ledger has no grade fields, distinguished from
explicit null fields. The checker requires no inference calls or source traces.

Extreme numeric JSON values outside finite floating-point representation are reported as invalid grades or scales rather than crashing. test_check_ledger.py covers both cases.

## Declared linked metadata agreement

`--match-reference-fields benchmark,domain,model,task_id,pass --unique-references` adds semantic agreement and injectivity to an existing-reference check. Shared fields must be present and equal on a slot and its referenced attempt; two slots cannot point to the same attempt. Unobserved slots with a null reference remain unlinked, and no ID is invented. These fields are explicitly declared rather than inferred by the generic checker. The full CMU reproduction command now enables these checks. Negative fixtures reject a wrong existing target, duplicate references and absent match fields.
