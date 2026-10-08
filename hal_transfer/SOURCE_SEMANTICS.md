# HAL source semantics and verification boundaries

The recorded Generalist evaluator commit is db2a824aa6a07ce8f1097258327fdfb7dd04c2ac. Exact official source SHA-256: 7d04be1e8fa92a6db0c535e490708dbb7a3605ff88ff05ea5d19e3ee4fa0090f. The source is downloaded with a pinned hash; no benchmark evaluation or model calls are executed here.

| Claim | Pinned primary source | Verification |
|---|---|---|
| String outputs are parsed as JSON | [evaluate_output lines180–186](https://github.com/princeton-pli/hal-harness/blob/db2a824aa6a07ce8f1097258327fdfb7dd04c2ac/hal/benchmarks/corebench.py#L180) | Source branch inspection; not merely hash equality |
| Parsing/evaluation exceptions receive zero correct-answer counts while preserving question totals | [exception branch lines198–205](https://github.com/princeton-pli/hal-harness/blob/db2a824aa6a07ce8f1097258327fdfb7dd04c2ac/hal/benchmarks/corebench.py#L198) | Source branch inspection plus all 45 raw evaluation records joined to ledger |
| Task success requires all written/vision answers correct | [get_metrics lines289–320](https://github.com/princeton-pli/hal-harness/blob/db2a824aa6a07ce8f1097258327fdfb7dd04c2ac/hal/benchmarks/corebench.py#L289) | Source branch inspection and archived task pass/fail lists |
| Exceptions map one-to-one onto 45 tasks | Immutable Generalist archive in source_manifest.json | Direct metadata join; 33 provider-credit and 12 client-message exceptions |
| Processed control exposes outcomes but lacks execution telemetry | Immutable control archive in source_manifest.json | Direct archive field inspection; null fields remain unknown |

Source hashes verify identity, source inspection establishes the declared grading interpretation, raw-field joins check extraction, and packaged-ledger replay checks arithmetic. None independently regrades task achievement. The adapter's simple source-string guard is not itself a proof of grading semantics. Raw datasets were available for the project checks but not redistributed to the simulated reviewers.
