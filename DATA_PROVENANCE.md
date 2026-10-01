# Data provenance for the denominator audit

Dataset: [cx-cmu/agent_trajectories](https://huggingface.co/datasets/cx-cmu/agent_trajectories)  
Downloaded: 28 September 2026 through the official Hugging Face CLI using the account granted access to the dataset.  
Repository revision recorded in the CLI local cache: `88e2af82c116a9a57f29be6f21b9924da081c2bd`.

The eight record files remain in `data/`. The study uses the six retained JSONL files and two JSON files containing later exclusions. `removal_log.json` and the dataset's [cleaning summary](https://huggingface.co/datasets/cx-cmu/agent_trajectories/blob/main/CLEANING_SUMMARY.md) provide the original-attempt and earliest-round exclusion counts. The earliest 329 removed records are not among the eight record files.

| File | Bytes | SHA-256 |
|---|---:|---|
| `mathhay.jsonl` | 678,662,533 | `e677e4fd64d4a69f1264db377003472f2b1fcc5b2bd6c2ea965474989057229a` |
| `mcpbench.jsonl` | 107,910,468 | `056d02cff3e888003c4de2a2fa05a6017adb3b7d8772ff210889cda6a33bf153` |
| `search.jsonl` | 160,074,333 | `701b282d9e2e6f6ebbe9cd0996c5c36cc8c12dcb725d775aa4b48921d1de7116` |
| `swebench.jsonl` | 150,701,297 | `361d3e13f0c72f743f2ffbe53960ab462b9e1027eaea0d15ec052b75fa10a24c` |
| `tau2bench.jsonl` | 67,082,285 | `8a691492668a3105219113f849d0bb9e23534789b37ce45b6b780ce2d3fd083c` |
| `terminalbench.jsonl` | 125,247,375 | `cd4a41777814ab53dfe2491c8567b33fdc4902fb2681e1450ef8b23ec6255860` |
| `removed_incomplete.json` | 131,083,743 | `f8755cf6fb2f7fdfa6713d842b6c3d289d3c55941683ca77c182f981201971e2` |
| `removed_truncated.json` | 45,982,530 | `cf0c3d14761f6ce1aa8e4354b4e6a44784a0634c2e33f2c1483fd54a6711d17b` |

Run `python3 audit.py` from this directory to regenerate `audit_results.json`. This analysis uses no model API.

## Independent WildClawBench case

Dataset: [internlm/WildClawBench-Trajectories](https://huggingface.co/datasets/internlm/WildClawBench-Trajectories). Downloaded 29 September 2026 through the official CLI. Pinned revision: `d2816016a7a7b41fa6b7ba368b28ddafcb54fd93`.

The 720-row `train.parquet` table contains the same 60 task IDs for each of 12 models. The score audit selects Claude Fable 5 because its raw-output archive was the smallest available, before examining scores. Its archive contains 60 score files; its session directory provides 60 status headers. This is a convenience sample for independent case evidence, not a random sample of models.

| File | SHA-256 |
|---|---|
| `train.parquet` | `9be080beb826b4c620d0a5d2987d1a0d3be758248076dfff48807fb11fcb4c17` |
| `output_claude_fable5.tar.gz` | `a95dd7e17205341d9ca3f46d8e499ea1225bb6ce35bc9e6a668f65140ac6c1f4` |

Run `independent_audit.py` using Python with PyArrow to regenerate `independent_results.json`. The audit reads archives in place and does not extract or execute archived files. `plot_results.py` uses Matplotlib to render the figure from both JSON audit outputs. The original native task scores are preserved even for explicit error-status runs.

The Open Agent Leaderboard summary was inspected as another candidate. Its aggregate fields use different notions of finished sessions and completed records, so it is not included as a quantitative replication in this draft.

## Metadata exports

The scripts export run accounting under `run_accounting/`; `verify_accounting.py` reconciles those exports with the audit summaries. Null availability in the WildClawBench ledger means unexamined source evidence, not a missing native source score. No trace text is included in the exports.

## Outcome-independent extension

EXTENSION_PLAN.json records the two additional archives selected by pinned file size before outcome inspection: Kimi K3 and GLM 5.2. Together with the original Claude Fable 5 case, extension_results.json covers 180 scores and session headers. source_hashes.json contains all 193 source-file hashes, including every status-header file. Model-level mean scores were reproduced from each archive before conditional analyses. Native stop reasons and exporter status are preserved separately.
