# Interval controls and external recorded-corpus recovery

Run from any directory using Python 3.10–3.12:

```
python submission/reproducibility/recovery_transfer/reproduce.py
```

To verify the saved outputs without rewriting them:

```
python submission/reproducibility/recovery_transfer/verify.py
```

This performs one fresh replay against the saved twice-replayed outputs and
checks pinned input/code hashes and unchanged original baseline summaries.

The reproduce command runs two fresh deterministic replays (270 cases, seven methods each),
independently reconstructs every final strict certificate using decimal
Fractions without the imported interval routine, checks the retrospective
oracle lower bound, and writes `results.json`, `per_case.csv`, source hashes,
and `verification.json`. No inference APIs, network access, or raw archives
are needed. Original source ledgers remain in their existing directories.

`PLAN.md` was saved before this extension produced results. Development is
outcome-informed after the old 90 WildClaw masks and prior HAL inspection;
this is not preregistration, an untouched holdout, or independent validation.
The original incumbent/challenger/wider policy is unchanged, using its existing
`select_next` function. The two fixed controls receive known grades, missing
identities and lexical identity order. Active-candidate traversal discards only
candidates whose upper endpoint is below the current largest lower endpoint
minus tolerance. Challenger-focused disclosure queries the largest upper rival
before the incumbent. Every method targets the same strict >1e-12 certificate.

The original WildClaw roster and exact 90 mask/retrieval seeds are retained.
HAL uses all five distinct archived source runs on their verified identical
45-task roster; it also reports the three previously size-selected mixed
archives separately. Different historical dates, model names, and scaffolds
make these archived-run recovery targets, not a capability comparison. No
run is dropped on its score; full-mean ties remain included with null oracle
and zero strict certificates. The two HAL rosters overlap and their results
are not independent environments.

HAL native scores use the archived evaluator convention: all task questions
correct, with parse errors assigned zero. One preexisting control archive has
only successful_tasks/failed_tasks labels, without raw grading records; its
ledger scores come from those archived labels. The extension verifies ledger
score availability, unit range, binary outcome agreement, archive hashes,
run/task uniqueness, and exact common support. It does not validate original
source extraction or achievement beyond these existing recorded ledgers.

Per-case CSV fields contain seeds, a canonical boolean-mask SHA-256, omitted
count, full-maximizer count, and costs/certificate flags. They contain no task
identities, task contents, grades, selected query logs, or raw archive rows.
Oracle null costs are blank. `results.json` reports all-case certificate
denominators, null/tie cases, paired costs and lower/equal/higher cost counts.
A lower cost on an unresolved tied roster does not mean successful recovery.
