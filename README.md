# Agent run accounting audit

Reproducible local audit of CMU agent trajectories and WildClawBench. The research examines corpus retention, documented attempts, native terminal roles and stop reasons, exporter status labels, and native task grades. No new agent execution or paid inference is required.

## Inputs and access

Use Python 3.10–3.12; install requirements.txt into a virtual environment. Install Hugging Face's `hf` CLI separately if needed. Use your own account and accept CMU's dataset conditions. Raw traces, source score archives, task artifacts, and credentials are not redistributed here. The complete source inputs require several gigabytes of downloads. Archive sizes for the three WildClawBench models are about 130 MB, 740 MB, and 747 MB; session files and CMU data are additional. Source_hashes.json verifies all 193 inputs, including 180 session files.

Run from this directory:

```sh
hf download cx-cmu/agent_trajectories tau2bench.jsonl swebench.jsonl terminalbench.jsonl mathhay.jsonl search.jsonl mcpbench.jsonl removed_incomplete.json removed_truncated.json removal_log.json --repo-type dataset --revision 88e2af82c116a9a57f29be6f21b9924da081c2bd --local-dir data
hf download internlm/WildClawBench-Trajectories train.parquet output_claude_fable5.tar.gz output_kimi_k3.tar.gz output_glm52.tar.gz --repo-type dataset --revision d2816016a7a7b41fa6b7ba368b28ddafcb54fd93 --local-dir independent_data/wildclaw
hf download internlm/WildClawBench-Trajectories --include 'sessions/claude_fable5/*.jsonl' --repo-type dataset --revision d2816016a7a7b41fa6b7ba368b28ddafcb54fd93 --local-dir independent_data/wildclaw
hf download internlm/WildClawBench-Trajectories --include 'sessions/kimi_k3/*.jsonl' --repo-type dataset --revision d2816016a7a7b41fa6b7ba368b28ddafcb54fd93 --local-dir independent_data/wildclaw
hf download internlm/WildClawBench-Trajectories --include 'sessions/glm52/*.jsonl' --repo-type dataset --revision d2816016a7a7b41fa6b7ba368b28ddafcb54fd93 --local-dir independent_data/wildclaw
python reproduce.py
```

Expected validation output includes reconciliation of 9,769 CMU released attempts plus 329 aggregate-only removals, 3,980 search slots, 720 WildClawBench released pairs, and 180 scored/status-joined runs. The verifier reads raw Parquet terminal events and native status headers; it also checks generated ledger/summary consistency. It does not independently regrade task artifacts or establish unpublished retry histories.

## Outputs

Final reporting outputs: extension_results.json, policy_comparison.json, SEARCH_DOMAIN_TABLE.md, and run_accounting/ after the full pipeline. independent_results.json and the illustrative figures preserve the historical initial one-model analysis. New corpora require extraction adapters for the reusable ledger schema in RUN_ACCOUNTING.md.

- audit_results.json: CMU benchmark/model/domain and four-pass summaries.
- independent_results.json: original one-model WildClawBench case.
- extension_results.json: three size-guided TAR-selected models on 60 shared tasks, with stop-reason/export-status comparisons.
- policy_comparison.json: complete search-model and model-by-domain summaries, group composition, and scoring-policy sensitivities.
- run_accounting/: metadata-only attempt/slot/pair exports. The original script exports the initial 60 scored runs; extension_audit.py replaces the WildClawBench pair ledger with all 180 examined runs. The remaining 540 pairs have null grade availability and status, meaning unexamined rather than absent source grades.
- figures/: descriptive PNG and SVG produced by plot_results.py (the initial illustrative comparison, not a complete three-model summary).

## Scope

CMU comparisons are exploratory. EXTENSION_PLAN.json records selection of the next two smallest TAR archives before reading their grades, following the original smallest-archive case. Two smaller ZIP archives were omitted; the original all-format selection description was inaccurate. The original plan and dated correction are preserved. These are three convenience-selected models, not a random sample of the full roster. The 720 released pairs cannot establish the absence of unpublished attempts. A source-documented scheduled grid and observed attempt IDs remain distinct.

Native scores are never silently overwritten. Exclusion-zero policies and conditional score means answer different questions. Exporter `completed` is a native label, not independently verified clean termination; some such records have aborted or length-limited native stop reasons. The analyses distinguish native grade from verified task achievement. RUN_ACCOUNTING.md documents the proposal and unknown-value rules.
