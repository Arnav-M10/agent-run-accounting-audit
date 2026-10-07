# Agent run-accounting audit

A local, no-inference audit of CMU agent trajectories and the complete pinned WildClawBench released roster. It separates retention, scheduled slots, observed attempts, final roles, native stop reasons, exported status, and recorded grades.

## Current coverage

- CMU: 9,769 released attempts plus 329 aggregate-only removals; 3,980 reconstructed search slots.
- WildClawBench: all 12 released models and 60 shared tasks, 720 recorded grades and terminal events; 600 available exporter-status headers. Two ZIP models have unknown exporter status.
- source_hashes.json: 624 pinned local inputs, including source documentation used to parse original-attempt counts.
- Grade means reproduce every model's released summary. This does not independently verify task achievement or unpublished retries.

## Acquire and reproduce

Use Python 3.10–3.12 and install requirements.txt in a virtual environment. Install Hugging Face's hf CLI separately and use your own authenticated account after accepting CMU dataset conditions. Raw inputs require about 8.64 GB for score archives, 201 MB for sessions, plus CMU and Parquet inputs. Raw traces, archives, task outputs, and credentials are not redistributed.

Run from this directory:

```sh
hf download cx-cmu/agent_trajectories tau2bench.jsonl swebench.jsonl terminalbench.jsonl mathhay.jsonl search.jsonl mcpbench.jsonl removed_incomplete.json removed_truncated.json removal_log.json README.md CLEANING_SUMMARY.md --repo-type dataset --revision 88e2af82c116a9a57f29be6f21b9924da081c2bd --local-dir data
hf download internlm/WildClawBench-Trajectories train.parquet --repo-type dataset --revision d2816016a7a7b41fa6b7ba368b28ddafcb54fd93 --local-dir independent_data/wildclaw
hf download internlm/WildClawBench-Trajectories --include 'output_*' --repo-type dataset --revision d2816016a7a7b41fa6b7ba368b28ddafcb54fd93 --local-dir independent_data/wildclaw
hf download internlm/WildClawBench-Trajectories --include 'sessions/*/*.jsonl' --repo-type dataset --revision d2816016a7a7b41fa6b7ba368b28ddafcb54fd93 --local-dir independent_data/wildclaw
python reproduce.py
```

If the archive transfer stalls, prefix the download with HF_HUB_DISABLE_XET=1 and add --max-workers 2. Extraction reads archives without executing task outputs. The pipeline reconstructs all ledgers, checks source hashes/joins/score means, and runs the reusable metadata checker.

## Final outputs

- full_roster_results.json: all 720 recorded grades, full-model conditional means, 600 status joins.
- terminal_measurement_results.json: role × native stop-reason and field-availability matrices for all 12 models.
- policy_comparison.json and SEARCH_DOMAIN_TABLE.md: all CMU search-model/domain and scoring-policy summaries.
- run_accounting/: final metadata-only attempts, slots, aggregate exclusions, and released pairs. All WildClawBench pairs have recorded grades; exporter status is null for the 120 ZIP-model pairs.
- ledger_check_results.json: checks of three real ledgers, all passing. See LEDGER_CHECKER.md for checker usage and limits.

Historical outputs: independent_results.json (initial one-model case), extension_results.json (three TAR models), zip_score_results.json (two ZIP models), and figures/ (initial illustrative comparison). Intermediate scripts overwrite the pair ledger; run the complete pipeline to restore the final full-roster export.

## Staged analysis and limits

EXTENSION_PLAN.json preserves the original inaccurate all-format smallest-archive description with a dated correction: two smaller ZIP archives were initially omitted. ZIP_EXTENSION_PLAN.json and FULL_ROSTER_PLAN.json record subsequent acquisition stages before their outcomes were inspected. Final coverage includes every released score archive, without outcome-based model exclusion. This fixed roster does not establish prevalence across all agent evaluations.

Exclusion-zero scoring and conditional means answer different questions. Native grades are preserved. Exporter completed is a recorded label, not independently verified clean termination. The generic checker verifies metadata consistency; corpus adapters and source checks establish joins. Neither independently regrades task achievement or recovers unknown retries or failure causes. RUN_ACCOUNTING.md gives the reporting proposal and a worked example.

The historical illustrative figure is optional: install requirements-plot.txt and run python plot_results.py. It is not used in the current manuscript or required for audit reproduction.

## Reuse the reporting tools

check_ledger.py validates explicit metadata identities, coverage, grade ranges, and references. summarize_ledger.py requires a missing-grade policy, declares inclusion rules, and emits populations, counts, coverage, scales, and means together. SUMMARIZE_LEDGER.md gives worked commands. demo_summarize_ledger.py independently matches all 46 available model-policy means. policy_order_results.json enumerates every model pair under each filter; it does not infer general rankings or correct original scores.

## Common task support

COMMON_SUPPORT.md describes an exploratory comparison of full-roster, separately selected, and shared-task score gaps. common_support_audit.py requires identical fully scored task rosters and explicit predicate equality. demo_common_support.py reports every pair under all three rules; common_support_results.json includes task IDs, counts and exact decomposition components. Seven focused support tests cover reversal classification, empty intersections, invalid rosters/grades/scales and typed missing-field handling. This is a descriptive support diagnostic, not a novel estimator, causal effect or corrected global ranking.

## Transfer to both corpora

REPORTER_TRANSFER.md gives executable retained and all-released CMU commands. The unchanged generic reporter matches twelve CMU benchmark/population means in addition to 46 WildClawBench model/policy means. Mixed native [0,1]/[0,10] pooling is rejected. Documentation-only exclusions remain outside the released-record ledger. demo_cmu_reporting.py and cmu_reporting_example.json contain checks and full outputs. This is internal arithmetic portability, not externally validated adoption.

## Coherence of pairwise task matching

COHERENCE.md and coherence_audit.py enumerate all triples for the existing predicates. Pair-specific task intersections produce four assistant and three native-stop directed cycles, with zero among exporter-status triples. coherence_results.json supplies every cycle edge, grade gap and task list plus global support sizes. The exploratory plan is preserved; cycles are observed population-dependent comparisons, not grader inconsistency or validated ability. Three additional tests exercise cycles, identical support and undefined comparisons.
