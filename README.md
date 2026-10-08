# Agent run-accounting audit

A local, no-inference audit of CMU agent trajectories and the complete pinned WildClawBench released roster. It separates retention, scheduled slots, observed attempts, final roles, native stop reasons, exported status, and recorded grades.

## Start with a reporting decision

Read [EVALUATOR_DECISION_GUIDE.md](EVALUATOR_DECISION_GUIDE.md) to choose the population and report only comparisons supported by available evidence. Try the tiny disclosed synthetic recovery example with `python3 recovery_diagnostics.py recovery_example_selected.jsonl --roster recovery_example_roster.json`. It needs only Python's standard library. Then verify the supplied ledgers below. Raw acquisition is a separate source-extraction check.

## Current coverage

- CMU: 9,769 released attempts plus 329 aggregate-only removals; 3,980 reconstructed search slots.
- WildClawBench: all 12 released models and 60 shared tasks, 720 recorded grades and terminal events; 600 available exporter-status headers. Two ZIP models have unknown exporter status.
- source_hashes.json: 624 pinned local inputs, including source documentation used to parse original-attempt counts.
- Grade means reproduce every model's released summary. This does not independently verify task achievement or unpublished retries.

## Verify the packaged ledgers first

From this directory, Python's standard library is sufficient for these checks; no model inference or raw-input acquisition is needed:

```sh
python3 -m unittest discover -s . -p 'test_*.py'
python3 check_ledger.py run_accounting/cmu_attempts.jsonl --identity attempt_id
python3 check_ledger.py run_accounting/cmu_search_slots.jsonl --identity benchmark,domain,model,task_id,pass --reference-ledger run_accounting/cmu_attempts.jsonl --match-reference-fields benchmark,domain,model,task_id,pass --unique-references
python3 check_ledger.py run_accounting/wildclaw_released_pairs.jsonl --identity model,task_id
python3 demo_cmu_reporting.py
python3 demo_summarize_ledger.py
python3 demo_common_support.py
python3 coherence_audit.py
```

These validate supplied metadata and reproduce 58 adapter means, task-support comparisons and graph diagnostics. They do not check extraction fidelity or independently validate task achievement. To reproduce extraction and source hashes as well, acquire the pinned raw inputs below and run the complete pipeline.

SOURCE_SAMPLE_CHECK.md documents a separate agent-assisted 35-record raw-to-ledger spot check, with zero field mismatches. Its script reconstructs sampled fields without the corpus adapters; selected identities and source hashes are preserved. This is a retained-record sample, not a full extraction or achievement validation.

EXCLUDED_SOURCE_CHECK.md extends the direct source check to 30 excluded CMU records, including targeted positive and zero saved rewards; all checked fields match. Reward stratification is disclosed. Original removal reasons/error flags are unavailable in the ledger and are not silently filled. Exact source counts confirm the 61 positive saved rewards.

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

COHERENCE.md and coherence_audit.py enumerate all triples for the existing predicates. Pair-specific task intersections produce four assistant and three native-stop directed cycles, with zero among exporter-status triples. coherence_results.json supplies every cycle edge, grade gap and task list plus global support sizes. The exploratory plan is preserved; cycles are observed population-dependent comparisons, not grader inconsistency or validated ability. Focused tests exercise cycle witnesses, margin profiles, identical support and undefined comparisons.

## Decision reporting extensions

`python3 mask_reference_audit.py` generates an exploratory joint-mask reference preserving coverage and overlap within six task categories. `python3 bounded_comparison.py` reports fixed-roster bounds and certified or unresolved comparisons in a disclosed masked-grade demonstration. Both use packaged data and only the standard library. See DECISION_EXTENSIONS.md and MASK_REFERENCE_PLAN.txt for assumptions, timing and limits. The 54 focused unit tests include exact bound endpoints and coverage geometry.

The bounds command also accepts an actually incomplete selected ledger and an explicit common task/model roster: `python3 bounded_comparison.py selected.jsonl --roster roster.json --score-range 0 1`. Source grades are not needed for omitted tasks. Leave-one-category-out reference sensitivity is available via `python3 mask_reference_sensitivity.py`.

`python3 mask_reference_block_sensitivity.py` reports the exploratory alternative category/difficulty blocking scheme; it uses fixed recorded grades to define lower/higher halves and does not establish exchangeability.

`python3 demo_cmu_bounds.py` applies the unchanged selected-ledger interface to the actual unavailable recorded grade in the reconstructed search roster; no attempt identity or score is invented. `python3 oracle_opportunity_audit.py` gives an exact, exploratory donor/thinning reference distinguishing observed pass opportunity from a remaining observed/reference discrepancy. See ORACLE_OPPORTUNITY_PLAN.txt for timing and unsupported cells.

## Recovery preflight and decision guide

EVALUATOR_DECISION_GUIDE.md maps available evidence to justified reporting choices. `python3 recovery_diagnostics.py recovery_example_selected.jsonl --roster recovery_example_roster.json` runs a disclosed synthetic example. The prototype reports pairwise optimistic grade-recovery counts and equal-weight interval leverage, not a guaranteed recovery policy, unique task priority, or simultaneous all-pairs budget. See RECOVERY_METHOD_PLAN.md for assumptions, proof and established prior-art overlap. Five added tests include exhaustive small binary recovery enumeration; all 54 tests pass. No real human adoption results are claimed.

## Concrete recorded-mean decision

`python3 winner_decision.py` reports all three existing completion predicates and an explicit released-roster target. Assistant and native-stop conditional means choose Claude Fable 5 rather than the full-roster recorded-mean maximizer GPT-5.6 Sol, a retrospective 5.178 percentage-point difference on that recorded target. Deliberately masked-grade winner reports leave 3/11/3 candidates and no certified strict maximizer. These are hypothetical reuse decisions, not observed consumer choices or deployment benefits. WINNER_DECISION_PLAN.md states the timing and assumptions; four added tests exhaustively verify small completion cases.

## Supplementary aggregate score-column check

`python3 aggregate_score_check/replay.py --output /tmp/aggregate_score_audit.json` reproduces every check on all 150 Open Agent Leaderboard aggregate rows. Six SWE-bench rows have different score columns and equal implied totals under complete numeric-grade coverage; the original aggregate Parquet lacks numeric-grade counts and individual outcomes. A separately pinned session release now verifies three actual within-run score-population contrasts; see session_score_check/. Historical generating joins and task-matched reversals remain unverified. The planned-equals-recorded subset shows four within-model score-column ordering reversals, not a verified third fixed-outcome denominator audit. Metric differences, unequal implied totals and unreported execution status coverage remain explicit. See [the supplementary audit](aggregate_score_check/README.md) for pins, all-row results, attribution, source semantics and limitations. This case is separate from the 624-input trajectory manifest and `reproduce.py`; it does not claim another generic-ledger transfer.

## Fixed-repeat recorded consistency

`python3 consistency_check/screen.py` reports every search model/domain cell, preserving the four-pass roster and separate retained task support. `python3 consistency_check/verify.py` exhaustively verifies all 995 nonlinear missing-grade bounds and 893 exact subset-size references. On the same 69 V3.2/BrowseComp tasks, full recorded consistency is 0.742754, uniform subsets matching retained counts give 0.800725, and actual retained subsets give 0.884461. This localized posthoc contrast reuses an existing metric, counts consistent failure as consistency, and does not establish latent reliability or a causal effect. All 15 cells, zero-retained tasks, actual versus deliberately omitted grades and source ledger hashes are explicit. See consistency_check/README.md.

## External HAL reporting transfer

hal_transfer/ contains an adapter and metadata from two pinned public archived HAL CORE-Bench runs: 90 records over 45 common task IDs. The same generic checker/reporter reproduces 0/45 and 19/45; 45 recorded task-mapped exceptions split 33 provider-credit errors and 12 client message-type errors. The original evaluator deliberately gives parse-error outputs known end-to-end zero grades. Those are not missing scores. Error-free inclusion has empty support and a null mean; control status remains unknown. The archived configurations differ and are not a capability comparison or representative HAL sample. Raw archives/traces are excluded; the source dataset has no inspected license/card metadata. Packaged metadata reporting is standard-library only; source reproduction additionally needs cryptography and two public downloads totaling under 1 MB. See hal_transfer/README.md for exact immutable source URLs, hashes, public decryption procedure and limits. No new inference or human participants are required.

`python3 hal_transfer/replay.py --verify-only` checks packaged HAL metadata offline with the standard library; raw acquisition/decryption is a separate route. Generic reports now separate known ineligibility from unknown eligibility and count each predicate's evidence. The linked-slot checker optionally verifies declared metadata agreement and one-slot-per-attempt references; the CMU pipeline enables both. These refinements preserve all existing reported means.

## Size-selected mixed HAL populations

hal_mixed_transfer/ adds three full CORE-Bench Generalist archives chosen by smallest byte size before inspecting scores; all three are reported. It reproduces 135 graded task/run records, joins all 1,965 archived calls to an identical 45-task universe, and pins each recorded evaluator commit. Two all-task scores tie at 4/45 but parse-error exclusion gives 4/44 and 4/5; the third remains 1/45. These conditional scores do not correct end-to-end accuracy or establish capability differences. The local prescore plan is not external preregistration and size selection is not representative. Source replay uses cryptography and approximately96.5MB public downloads; no inference or raw redistribution. See the case README for exact pins, coverage and limits.

## Actual consumer and disclosure evidence

consumer_reuse/ verifies all5,315 retained CMU trial-grade multisets in a public consumer, across1,465 task/model groups, and replays its observed-trial task-mean reduction on all15 Search cells. Source acquisition verifies the full593.5MB checksum and extracts only private grade/identity metadata. It does not reproduce published IRT/frontier results or original pass identities.

`python3 winner_recovery.py run_accounting/wildclaw_released_pairs.jsonl` emits simultaneous exact offline certificate counts and one fixed revealed-grade-only selector. All3masks reported: oracle5/60/2, selector5/76/2, restore-all54/175/33. These are simulated disclosures of existing grades, not deployment gains. `python3 verify_winner_recovery.py` checks4,096binary and150fractional fixtures plus exact tolerance regressions. WINNER_RECOVERY.md explains established-query-method positioning and equal-weight/unit-cost assumptions.

session_score_check/ replays actual grade/status populations in three named public SWE session runs, including28/100vs28/38. Shards/session rows excluded; code/checksums/run-level summaries only. PyArrow required for raw replay. This supplements, but does not replace, the conditional150-row historical aggregate audit.

## One verification entry for new evidence

`python3 verify_new_evidence.py` verifies packaged disclosure results and exhaustive fixtures with the standard library. Optional `--consumer-metadata PRIVATE_ACQUIRED_METADATA` verifies the pinned private consumer cache and every group/reduction. Optional `--session-shards PRIVATE_PARQUET_DIRECTORY` verifies all nine source hashes and three session score populations; requires PyArrow. The command makes no downloads or inference calls and keeps scratch outputs in a temporary directory. It explicitly distinguishes packaged replay, private derived-cache verification and raw source replay. Acquisition instructions remain in each case README.
