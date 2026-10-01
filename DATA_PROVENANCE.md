# Data provenance and staged analysis

## Pinned releases

CMU: cx-cmu/agent_trajectories, revision 88e2af82c116a9a57f29be6f21b9924da081c2bd. Inputs are six retained JSONL benchmarks, removed_incomplete.json, removed_truncated.json, removal_log.json, README.md, and CLEANING_SUMMARY.md. The original-attempt and first-round counts are parsed from the pinned cleaning table. The source documents contain aggregate-only information for 329 exclusions, not released execution IDs.

WildClawBench: internlm/WildClawBench-Trajectories, revision d2816016a7a7b41fa6b7ba368b28ddafcb54fd93. Inputs are train.parquet, all 12 score archives, and all 600 released session files from ten model directories. The table is 12 models by the same 60 tasks. Two ZIP models have native grades but no released exporter-session directories at this revision; their exporter status remains unknown.

## Historical stages and corrected selection description

The initial Claude Fable 5 case was followed by a TAR-only extension to Kimi K3 and GLM 5.2. The original plan inaccurately described the chosen TAR archives as the smallest across all formats, omitting two smaller Qwen ZIP files. EXTENSION_PLAN.json preserves that original text and a dated correction; it does not retrospectively claim TAR-only eligibility was preregistered.

ZIP_EXTENSION_PLAN.json records adding both ZIP models after the three-model results and before reading their scores. FULL_ROSTER_PLAN.json records subsequently acquiring the remaining seven score archives and every available session directory. Final full-roster results cover the entire pinned released roster; the original staged summaries remain historical outputs.

## What is verified

Source_hashes.json pins every local source input. Source-to-ledger checks compare all terminal event roles/reasons, join every available native session header, and preserve each recorded native score. Each model's all-task mean is reproduced from its archive summary before alternative filters are calculated. Original events, synthetic export warning markers, exporter status, and native stop reasons remain distinct.

No archived task outputs are executed. Raw archives, traces, and credentials are not redistributed in the public artifact. The analyses are local and require no new model execution or paid inference. Verification checks recorded evidence, not independent task achievement, unreleased retries, or causal failure attribution.
