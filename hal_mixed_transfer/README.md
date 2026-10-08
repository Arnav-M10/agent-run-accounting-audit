# Size-selected HAL mixed-status transfer

Three official full CORE-Bench Generalist archives were selected by byte size (lexical filename tiebreak) before scores were inspected. The already inspected all-error run and slim archives were excluded. No remaining candidate fit a 10MB total budget; the allowed alternative budget of three smallest full archives was used, totaling 96,494,907 bytes. `selection_plan.json` records all 32 candidates and all three selections; all three are reported, including the run with zero recorded errors.

| Historical archived run | Source passes / all tasks | Recorded parse errors | No recorded parse error score | Archived call exception tasks |
|---|---:|---:|---:|---:|
| DeepSeek V3-0324, Aug 20 2025 | 4/45 (8.89%) | 1 | 4/44 (9.09%) | 1 |
| DeepSeek R1, Sep 11 2025 | 1/45 (2.22%) | 0 | 1/45 (2.22%) | 0 |
| Claude 3.7 Sonnet, June 1 2025 | 4/45 (8.89%) | 40 | 4/5 (80%) | 0 |

The unchanged canonical checker validates 135 unique run/task rows, all known binary grades. Every run has the same 45 task IDs. All archived calls join exactly to these tasks: 458 V3 calls, 546 R1 calls, 961 Sonnet calls; no unmatched calls. The unchanged reporter reconstructs the three published scores and all conditional means.

The two 4/45 runs tie under the published end-to-end rule, while their different valid-parsing populations yield different conditional means. This is observed population sensitivity; it is not a score correction, rank reversal, or model capability comparison. All three native evaluator files at their respective run-recorded commits have identical bytes and explicitly assign zero correct answers on parsing exceptions. Known parse-error zeros are not missing grades. The conditional means condition on an outcome-related response property and should not replace end-to-end accuracy.

`parse_error_present=false` means the raw evaluation record has no error field under this source-specific evaluator; it does not mean the science task was solved. `logged_exception_present=false` means no exception among archived call records for that task, not proof of complete successful execution. In particular, the Sonnet run has 40 parser errors despite no archived call exceptions. Neither mask is called completion. No human grades or new inference were generated.

## Replay

Run `python reproduce.py` with Python's cryptography package available. Raw public archives use a temporary cache that is removed after replay. For a private persistent cache outside this folder, use `python reproduce.py --cache-dir /private/tmp/aes_hal_mixed_cache`.

Downloads use official dataset revision `e7dcedc82b4f4bc819a170fd6616bdb44841c71e`, full SHA-256 verification and run-specific evaluator commits. Decryption implements the official documented public `hal1234` password and algorithm, without guessing. `source_manifest.json` pins official encryption sources and byte-identical canonical reporting code. Raw traces and benchmark contents are excluded from this directory; only derived task/grade/status metadata are retained. Dataset license/card metadata remain unknown.

Current leaderboard or paper inclusion of these historical archives is not established. Selection by smallest archive size is reproducible but not representative of HAL. Configurations differ in model/date/budget/scaffold implementation. No prevalence, causal, capability, or universal generalization claim follows. HAL already studies infrastructure failures and exclusions; this case contributes reproducible external-corpus transfer of the same reporter and observed mixed-status population sensitivity.

The prior all-error case is preserved separately and supplies the true empty-support check. This mixed case supplies nonempty eligible and ineligible subsets with available source grades. The manual Opus4.5 uplift remains unverified aggregate provenance; it is not used here.

## Files

- `selection_plan.json`: fixed inventory-based plan, selected before scores.
- `reproduce.py`: own adapter, pinned fetch/decryption, task-ID joins, assertions; calls unchanged canonical reporter/checker.
- `hal_mixed_ledger.jsonl`: 135 derived task-run grade/status metadata rows.
- `verification.json`, `reporter_results.json`, `ledger_check.json`: results and verification.
- `source_manifest.json`: immutable primary-source URLs and file hashes.

Primary sources: [official HAL dataset](https://huggingface.co/datasets/agent-evals/hal_traces), [official harness](https://github.com/princeton-pli/hal-harness), [HAL paper](https://arxiv.org/html/2510.11977v1). The three dataset archives and recorded evaluator commits are directly pinned in the manifest.
