# Open Agent Leaderboard: conditional aggregate denominator audit

This package retains every original aggregate field for all 150 released rows. It does not contain traces or task-level records.

## Replay

`python3 replay.py --output audit_results.json`

Replay requires only the Python standard library and `released_aggregates.json`. Source-to-derived conversion is included as `extract.py` and uses PyArrow. For this environment:

```sh
PYTHONPATH=/private/tmp/aes-oct5-pyarrow /Users/arnav/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 extract.py --parquet /Users/arnav/Documents/AES/independent_data/open_agent_leaderboard/data/train-00000-of-00001.parquet --output reproduced_aggregates.json
python3 replay.py --input reproduced_aggregates.json --output reproduced_audit.json
```

The extractor checks the pinned parquet SHA256. Both extractor and replay validate 150 unique keys, the full 5 x 5 x 6 grid, finite scores in [0,1], and finite nonnegative integer counts. Replay does not require PyArrow. Re-extraction was verified byte-identical to `released_aggregates.json`. JSON row order equals original parquet row order. The script uses absolute tolerance 1e-8 and retains every mismatch/status gap rather than silently dropping anomalous rows.

## Pins

Dataset: https://huggingface.co/datasets/open-agent-leaderboard/results

Revision: `0e6034d9d4aad1dfa77480f6f62d007fe2f040e3`; metadata lastModified `2026-05-18T12:51:21.000Z`.

Local and independently downloaded official pinned parquet SHA256: `8bea4f9c00f789f2410d9b7824f138abea348c37a6bc51f6fd7d4b4b24ee271a`.

Source review pin: `8af99b17c7b5c6a32f7578ff3a7c9e3d0f389fa5`, latest main commit preceding that metadata timestamp. This is not known to be the data-generating commit. The dataset does not record its generating source version. Individual source file hashes are in `released_aggregates.json` provenance. Current source `ae8d10f7f1e29d2b08d8a5d41bafa16836004998` agrees on the checked definitions.

Paper: https://arxiv.org/html/2602.22953v1, section 4.3. It defines success by the benchmark's original evaluation; it does not establish the particular denominators below.

## Source definitions and metric identity first

At the source review pin, prefix all paths below with:
https://github.com/Exgentic/exgentic/blob/8af99b17c7b5c6a32f7578ff3a7c9e3d0f389fa5/

* `src/exgentic/observers/handlers/results.py#L346`: total_sessions = length of recorded result snapshot.
* `src/exgentic/observers/handlers/results.py#L362`: successful_sessions counts truthy session success.
* `src/exgentic/observers/handlers/results.py#L364`: average_score averages **non-null numeric scores**. Its denominator is not total_sessions by definition. The release lacks numeric-grade count.
* `src/exgentic/core/orchestrator/run.py#L131`: only execution-COMPLETED sessions are supplied to benchmark aggregation.
* `src/exgentic/core/types/session.py#L147`: execution-INCOMPLETE includes error/cancelled/unknown outcomes and session directories without result files. Unfinished and limit outcomes can count as execution-COMPLETED. This is not a missing-grade count.
* `src/exgentic/benchmarks/swebench/swebench_eval.py#L422`: averages per-session numeric benchmark score over supplied completed sessions.
* `src/exgentic/benchmarks/swebench/swebench_logs.py#L30` and `#L151`: numeric score is binary issue resolution.
* `src/exgentic/benchmarks/swebench/swebench_logs.py#L144`: session success means harness error is None, not issue resolution. successful_sessions must never be labeled resolved count.
* `src/exgentic/benchmarks/appworld/appworld_eval.py#L403`: numeric session score is passed-test percentage; `#L632`: benchmark primary score is task_goal_completion. These are different metrics; exclude from denominator-only comparisons.
* `src/exgentic/benchmarks/browsecompplus/browsecomp_benchmark.py#L519`: aggregation reads correctness/success; published score columns agree in all 25 rows. Eleven rows have absent status coverage (zero completed/incomplete/missing despite positive planned/recorded counts).
* `src/exgentic/benchmarks/tau2/tau2_eval.py#L523` and `#L667`: session reward versus aggregate avg_reward. Cross-artifact numeric-grade coverage/comparability not established here; retain descriptive differences but exclude from denominator-only ordering analysis.

## Eligibility and limitations

Products `average_score * total_sessions` are **implied totals conditional on every recorded result having a non-null numeric score**. Products `benchmark_score * completed_sessions` use the source-supported completed-session aggregation denominator. Equal products do not verify actual equal numerators or an identical task-level outcome vector. No task IDs or individual grades are released in the parquet. All candidate eligibility in this package is conditional on numeric-grade coverage; it is not a verified empirical third case under a requirement for exact same outcomes.

Conditional recorded-denominator eligibility: SWE-bench; positive recorded and completed counts; equal implied numeric totals; both implied totals integral within tolerance. Strict eligibility adds planned_sessions == total_sessions. Pairs are within the same model among rows eligible under the selected rule; comparisons keep ties separate from strict reversals. Recorded denominators may differ from planned workload; the strict filter removes those rows, but cannot establish identical tasks across agents. No planned-session imputation is performed.

Two SWE-bench rows (ReAct and ReAct + Shortlisting with GPT-5.2) have the same recorded/completed denominator 100 but average_score .58 and benchmark_score .57, implying different totals 58 and 57. They are retained and excluded from candidate denominator attribution. Claude Code/GPT-5.2/Tau2 retail has .51 versus .64 at counts 100/100 and is likewise not denominator-only evidence.

ReAct and ReAct + Shortlisting have identical SWE aggregate values across all five models. Pairwise comparisons count configuration rows, not independent evaluations; no statistical inference is justified.

## Full 150-row counts

| Benchmark | Rows | Different scores | Positive incomplete | Planned != recorded | Status coverage gaps | Conditional eligible | Strict eligible |
|---|---:|---:|---:|---:|---:|---:|---:|
| AppWorld | 25 | 22 | 11 | 0 | 0 | 0 | 0 |
| BrowseComp+ | 25 | 0 | 6 | 0 | 11 | 0 | 0 |
| SWE-bench | 25 | 8 | 8 | 4 | 0 | 23 | 19 |
| Tau2 airline | 25 | 0 | 0 | 0 | 0 | 0 | 0 |
| Tau2 retail | 25 | 1 | 4 | 3 | 0 | 0 | 0 |
| Tau2 telecom | 25 | 0 | 2 | 1 | 0 | 0 | 0 |

150 distinct agent/model/benchmark keys. missing_sessions is zero for all 150 rows; this does not establish grade coverage. Status coverage gap is planned minus completed+incomplete+missing and is flagged in 11 BrowseComp+ rows. The release has no running_sessions column; that unavailable category is omitted. These are descriptive status coverage gaps, not proven contradictions.

Six conditional SWE discrepancy candidates have equal implied totals: Claude Code/Kimi 51 over 99 vs 98; Solo/DeepSeek 28 over 100 vs 38; Solo/Kimi 55 over 100 vs 97; Smolagent/Kimi 53 over 93 vs 92; ReAct/DeepSeek and ReAct+Shortlisting/DeepSeek 66 over 100 vs 96.

Conditional recorded analysis: 43 within-model pairs, six strict ordering flips, zero tie changes. Strict analysis: 33 pairs, four strict flips, zero tie changes. The four strict flips involve Solo/DeepSeek versus each other DeepSeek configuration. Two additional recorded-only flips involve Smolagent/Kimi versus ReAct and ReAct+Shortlisting/Kimi.

## Strongest illustrative pattern, conditional only

DeepSeek Solo releases average_score .28 and benchmark_score .7368421052631579, with planned=recorded=100 and completed=38; equal implied totals are 28. Claude Code releases .64/.64 with completed=recorded=100. The published ordering therefore reverses between score columns. Solo successful_sessions is 38 (harness success), not 28 (implied resolved total). Under complete numeric-grade coverage, this is consistent with 28/100 versus 28/38. Without that coverage evidence, it is an aggregate pattern requiring further validation before claiming fixed-outcome denominator attribution.

No inference runs or paid API calls are required. Raw task traces are not included.

## Source file hashes and direct pinned links

* [src/exgentic/observers/handlers/results.py](https://github.com/Exgentic/exgentic/blob/8af99b17c7b5c6a32f7578ff3a7c9e3d0f389fa5/src/exgentic/observers/handlers/results.py); SHA256 `1c7207620f9ba3eb7a788343b45bc83b1a0acad9113765de069462fc1197b6f2`
* [src/exgentic/core/orchestrator/run.py](https://github.com/Exgentic/exgentic/blob/8af99b17c7b5c6a32f7578ff3a7c9e3d0f389fa5/src/exgentic/core/orchestrator/run.py); SHA256 `8c36cb4fab318598683f2d48808aab0c1f0560b4af02a33694523c8c76d0deb3`
* [src/exgentic/core/types/session.py](https://github.com/Exgentic/exgentic/blob/8af99b17c7b5c6a32f7578ff3a7c9e3d0f389fa5/src/exgentic/core/types/session.py); SHA256 `2cb331528cd8a741c7d032d598ddd8e3a3ebeec122b25abf58e1279222e059ff`
* [src/exgentic/benchmarks/swebench/swebench_eval.py](https://github.com/Exgentic/exgentic/blob/8af99b17c7b5c6a32f7578ff3a7c9e3d0f389fa5/src/exgentic/benchmarks/swebench/swebench_eval.py); SHA256 `27e3d5a42f3b6119f4ac2a3a0b1d0628fdf50c9e420dce89a1244ea95fbb095b`
* [src/exgentic/benchmarks/swebench/swebench_logs.py](https://github.com/Exgentic/exgentic/blob/8af99b17c7b5c6a32f7578ff3a7c9e3d0f389fa5/src/exgentic/benchmarks/swebench/swebench_logs.py); SHA256 `6026744614d80ba32a75d0992a70c5a4f4ba6226fd9dd54b6ee7ac229139dc8a`
* [src/exgentic/benchmarks/appworld/appworld_eval.py](https://github.com/Exgentic/exgentic/blob/8af99b17c7b5c6a32f7578ff3a7c9e3d0f389fa5/src/exgentic/benchmarks/appworld/appworld_eval.py); SHA256 `50fdb95ebe4106005940d7d398d0388f4877110925e8d1c8a8431ad3cc88725b`
* [src/exgentic/benchmarks/browsecompplus/browsecomp_benchmark.py](https://github.com/Exgentic/exgentic/blob/8af99b17c7b5c6a32f7578ff3a7c9e3d0f389fa5/src/exgentic/benchmarks/browsecompplus/browsecomp_benchmark.py); SHA256 `896a73c3ecbf32e98fd488fdefac44356d2b5d13ed4fd906c655a717bb145a31`
* [src/exgentic/benchmarks/tau2/tau2_eval.py](https://github.com/Exgentic/exgentic/blob/8af99b17c7b5c6a32f7578ff3a7c9e3d0f389fa5/src/exgentic/benchmarks/tau2/tau2_eval.py); SHA256 `84c153f0b1c3ffd06e57f8d42883d5b445f1b551b71c0536a09b89a4d3dbad85`

## Packaging verification

The JSON audit was regenerated after schema changes. Its 150 rows include original scores/counts and explicit conditional eligibility; no actual resolved total is asserted. Source extraction reproduced the full aggregate JSON byte-for-byte.

## Data attribution and license

Aggregate fields originate from Open Agent Leaderboard Results at the pinned Hugging Face revision above, released under CDLA-Permissive-2.0: https://cdla.dev/permissive-2-0/. The full license text is included as CDLA-Permissive-2.0.txt. This derived JSON is an attributed aggregate-field conversion, not individual task trajectories.

To re-extract after downloading the pinned Parquet, run `python3 extract.py --parquet /path/to/train-00000-of-00001.parquet --output released_aggregates.json` with PyArrow installed. The pinned hash is required; replay remains standard-library only.

## Later session evidence

The original aggregate artifact still lacks individual outcomes. Separately pinned session_score_check/ now checks actual100-session grade vectors for three configurations, reproducing their two released score columns. Historical aggregate-to-run linkage and common task support remain unavailable; conditional rank reversals are not promoted to verified cases. See the adjacent package for source hashes and raw replay.
