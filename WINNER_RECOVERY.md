# Global recorded-winner disclosure

`winner_recovery.py` is portable when placed beside existing `mask_reference_audit.py` and `bounded_comparison.py`. Standard library only. It writes nothing unless `--output` is explicitly supplied. All simulation grades must already be available in the input ledger; unavailable-grade inputs are intentionally rejected rather than fabricated.

Run from the reproducibility directory with the packaged module:

```
python3 winner_recovery.py run_accounting/wildclaw_released_pairs.jsonl --output winner_recovery_results.json
```

Verification: `python3 verify_winner_recovery.py`.

`select_next(known, missing, models, tasks)` is the only adaptive selection function. It does not receive the truth array, full means, winner identity, or the offline result. Its return value is chosen before the caller accesses `grades[m][t]`. Every query log preserves pre-query interval endpoints and missing counts, then the queried identity and newly revealed grade. Initial unmasked known grades and each log step suffice to reconstruct the selector state. The exact offline oracle lives separately in `optimal`, which deliberately uses all recorded grades.

With tied maximizers the offline minimum is null; the independent policy still runs until it establishes that no strict certificate is available. It does not use the oracle winner to select disclosures. No new inference, human annotation, paid API, or network action occurs.

Tests: exhaustive all 4,096 binary 3-model/2-task grade-mask fixtures; all disclosure subsets brute-forced for minimum certificate size; 150 seeded fractional 3-model/3-task fixtures brute-forced; policy correctness and oracle lower-bound comparison on all 2,112 exhaustive unique-winner fixtures. These exercise shared winner-query gains, uncertain incumbents, partial masks, zero/full availability, and tied winners.

## Numerical convention

Oracle feasibility, selector decisions and certificate validation interpret canonical JSON numeric decimals as exact rational values. The strict native-scale tolerance is exactly 1e-12. Float values are used only to display output intervals. This avoids inconsistent decisions when accumulated binary rounding straddles the tolerance. A separate checker reproduced every released query and found the near-tolerance counterexample that prompted this correction. The verifier includes that regression, 4,096 exhaustive binary fixtures and 150 fractional brute-force fixtures. No claim of new general uncertainty-query theory is made.
