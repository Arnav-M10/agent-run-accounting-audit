# HAL task-level reporting transfer

This directory contains an adapter and derived metadata from two pinned public archived HAL CORE-Bench runs. No raw trace, benchmark question, agent answer, credential, or encrypted archive is distributed here. No new inference or human evaluation is performed.

## Offline packaged-metadata replay

`python3 hal_transfer/replay.py --verify-only` from the artifact root checks saved reports and pinned reporter-file hashes with only Python's standard library. It distinguishes 45 known ineligible Generalist records from 45 unknown-eligibility controls; both selected means remain null. This checks packaged metadata, not raw extraction.

## Reproduce source extraction

Use Python with `cryptography` available. The reporting/checking code otherwise uses only the standard library. Run:

```
python hal_transfer/reproduce.py
```

The adapter downloads two public archives totaling 947,927 bytes plus three small official source files using curl. By default it keeps raw archives in a temporary directory and removes them after the run. To keep a private raw cache outside this release directory:

```
python hal_transfer/reproduce.py --cache-dir /private/tmp/aes_hal_raw_cache
```

Decryption follows the official publicly documented `hal-decrypt` implementation exactly: password `hal1234`, PBKDF2-SHA256 with 480,000 iterations and Fernet. It does not guess a password. Downloads use immutable dataset/code commits and SHA-256 verification. The dataset is public and ungated but has no license/card metadata in the inspected official repository. Raw redistribution is excluded. See `source_manifest.json` for complete pins and hashes.

## What is verified

The ledger has 90 unique `(run_id, task_id)` identities and 45 shared task IDs. Every row has a known native binary grade, and the generic `check_ledger.py` passes with zero issues. The generic `summarize_ledger.py` reconstructs the archived 0/45 Generalist score and 19/45 Claude Code Opus 4.1 score without grade imputation. File hashes in `source_manifest.json` establish reporter identity; copied tools are byte-identical to their canonical counterparts.

Generalist records expose 45 parse errors and exactly 45 task-mapped exception calls in 57 recorded calls: 33 provider credit errors and 12 client message type errors. At the run's recorded evaluator commit, parse errors assign zero correct answers and preserve question totals; these are known end-to-end failures under the source grading rule. They are not missing grades or proof that the aggregate calculation was wrong.

The Claude Code archive exposes pass/fail task lists, but no raw evaluation records or call logs. Its status fields are explicit null/unknown. A pass is not treated as evidence of an exception-free trace, and absence of telemetry is not treated as a clean execution status.

The existing reporter's equality rule `parse_error_present=false` excludes all 45 observed-error Generalist tasks and also excludes 45 control tasks whose status is unknown. Each mean is null/undefined because the selected population is empty. Those groups have different explanations: known all-error population versus uncertifiable control status. The `logged_exception_present=false` report behaves analogously. No synthetic exception-free row or outcome is created, and no missing-grade policy assigns zero to these groups.

## Scope and limits

The two configurations differ in date, model, budget, and scaffold. Their scores are not a controlled capability comparison. The Generalist archive is a historical public run selected because it is small and exposes direct operational failures; membership in the current leaderboard or the HAL paper's analyzed runs has not been established. Do not estimate HAL failure prevalence or claim a denominator reversal.

The contribution is a deterministic cross-corpus reporting transfer and a real empty-support example. HAL already reports infrastructure failures, trace analysis, evaluator bugs, and exclusions. This case does not discover failure-aware evaluation or validate AES users' decisions.

The official CORE-Bench page also displays 77.78% for a separate Opus 4.5 run and 95.5% with manual validation. The selected tiny Opus 4.5 archive inspected during feasibility had the original 35/45 labels. No corrected task-label mapping was found; this directory does not reconstruct, infer, or validate that manual correction. The original-versus-corrected contrast remains an aggregate provenance limitation.

## Files

- `reproduce.py`: source-pinned downloader, deterministic decryption and metadata adapter, assertions, calls to generic checker/reporter.
- `hal_task_ledger.jsonl`: derived run/task IDs, binary source grades, explicit status metadata and source archive hashes.
- `ledger_check.json`: generic checker output.
- `reporter_results.json`: generic reporter output for published and explicitly error-free populations.
- `verification.json`: exact population/status assertions and limitations.
- `source_manifest.json`: immutable primary-source URLs and SHA-256 hashes; unknown dataset license declaration.
- `summarize_ledger.py`, `check_ledger.py`: unmodified canonical AES implementation copied for self-contained replay.

Primary sources: official [HAL dataset](https://huggingface.co/datasets/agent-evals/hal_traces), [HAL CORE-Bench page](https://hal.cs.princeton.edu/corebench_hard), [run-pinned evaluator](https://github.com/princeton-pli/hal-harness/blob/db2a824aa6a07ce8f1097258327fdfb7dd04c2ac/hal/benchmarks/corebench.py), and [HAL paper](https://arxiv.org/html/2510.11977v1).

The eligibility-reporting refinement adds evidence counts without changing any selected population or mean. Both corpora use the same implementation with no HAL-specific reporting branch. SOURCE_SEMANTICS.md links the exact source branches and distinguishes source identity, interpretation, extraction and arithmetic checks.
