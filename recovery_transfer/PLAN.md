# Frozen local recovery comparison plan

Written 2026-10-08 before running this extension. This is an outcome-informed
local plan after the original 90 WildClaw masks and prior HAL ledger inspection;
it is not preregistration, independent validation, or an untouched holdout.
No new inference, paid APIs, or source acquisition.

Keep the incumbent/challenger/wider policy and original lexical, randomized,
offline oracle, restore-all baselines unchanged. Add exactly two fixed controls.
All controls receive only known grades, missing identities, and sorted identities:

* Active-candidate traversal: compute largest lower bound L; active candidates
  have upper bound >= L - tolerance. Query the first lexical missing (run,task)
  among active candidates. Recompute after each disclosure. Stop on the same
  strict certificate, or if no active candidate has missing grades.
* Challenger-focused: select largest-lower incumbent (lexical ties), then
  largest-upper rival (lexical ties). Query that rival's first lexical missing
  task; if it has none, query incumbent's first missing task; if neither has
  any, stop unresolved. Recompute after every disclosure.

Every decision first checks strict interval dominance, with exact Fractions and
1e-12 tolerance imported from winner_recovery. Controls never consult withheld
grades before choosing the next cell. No policy tuning after outputs.

Run the identical 90 original WildClaw masks: Bernoulli omission rates .1, .25,
.5, thirty seeds each, seed 2026100800 + 1000*rate_index + seed_index; random
retrieval seed 2026101800 + 1000*rate_index + seed_index. Apply the same rules to
HAL's all five archived runs if all share exactly 45 unique task identities,
and separately the three size-selected mixed archives. Run identity is source
run_id, not any duplicated model name. Historical dates/scaffolds differ; this
is external-corpus computational transfer, not a capability comparison.

Keep all cases including full-mean ties; no mask filtering or resampling. A
full-mean tie means no strict certificate and null oracle; report this explicitly.
For every case save roster label, rate, seeds, mask hash, omitted count, all
method costs and certificate flags without task identities or grade contents.
Validate source score availability/range, uniqueness, archive/run identity,
complete common support. Independently reconstruct every final certificate
without the imported bounds function; confirm oracle lower bounds on all
nonnull cases. Replay deterministically and compare aggregate and per-case bytes.
Save code, source hashes, results, per-case CSV, README and verification.
