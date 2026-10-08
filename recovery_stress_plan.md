# Frozen retrospective winner recovery stress plan

Frozen before execution on 2026-10-08. This experiment uses the existing fully
recorded Wild 12-model by 60-task matrix, including every model and task. It
performs no inference calls and publishes aggregate outputs only.

For each omission probability 0.10, 0.25, and 0.50, run exactly 30 seeds indexed
0 through 29. Each of the 720 cells is independently withheld with probability
p by Python random.Random(2026100800 + 1000 * rate_index + seed_index), in sorted
model and task order. Rates are independently seeded. No rejection, resampling,
outcome-conditioned selection, category restriction, or case filtering is
permitted. This gives 90 cases, including any already-certified or difficult
case. No coverage constraints are imposed.

Target: the unique strict maximizer of the equally weighted full recorded-grade
mean, using the existing winner_recovery exact-decimal arithmetic and tolerance
1e-12. Full-mean ties within that tolerance remain in the results; no strict
certificate can be obtained for them. Report their count and keep all cases in
certificate-rate denominators. A certificate requires one observed lower bound
to exceed every other model's upper bound by more than that tolerance.

Compare five methods on exactly the same masks:

1. Existing winner_recovery.adaptive selector-blind policy: largest lower-bound
   incumbent, largest upper-bound challenger, query the wider of those intervals,
   and break identity ties lexicographically. Only queried grades are revealed.
2. Grade-blind lexicographic retrieval: fixed sorted (model, task) order, stopping
   at the first strict certificate.
3. Grade-blind randomized retrieval: shuffle omitted slots using the separate
   random.Random(2026101800 + 1000 * rate_index + seed_index), stopping at the
   first strict certificate. The random order never uses held-out grades.
4. Existing winner_recovery.optimal offline oracle minimum using actual grades;
   it is a retrospective lower bound, not a usable prospective query policy.
5. Restore all omitted cells, then check the strict certificate.

Queries mean retrievals of already recorded omitted grades, not new rollouts or
new grading. Report per-rate certificate rates, query mean/median/nearest-rank
5th and 95th percentiles/range, fraction of available omitted grades retrieved,
paired query differences, and counts of positive omitted winner grades and cases
with at least one. Report oracle and restore-all query costs with the same
case denominator. Oracle costs for tied full winners are null and explicitly
counted; no strict-success-conditioned query summary replaces the all-case costs.

Validate every certificate against the full exact means and reconstructed
post-retrieval intervals, every oracle certificate, and oracle cost <= each
other method's cost in every case where a strict full winner exists. Validate
all 90 cases complete and no raw row identities or grades enter the saved
results. Repeat the complete deterministic experiment and require byte-identical
canonical aggregate results. Record hashes of this plan, the program, input,
and imported winner_recovery module to make the run auditable.

Interpretation is confined to stress-testing interval winner recovery after
independent artificial withholding on this released roster. These masks do not
model deployment missingness, the matrix is not an independent validation set,
and no deployment benefit, generalization guarantee, achievement validation,
or prospective oracle budget is claimed.

## Explanatory amendment after execution began

After the initial execution had begun, before any aggregate output was delivered,
we added this clarification and restarted execution to record the final plan
hash: this is an outcome-informed extension developed after earlier analyses,
with sampling and comparison choices frozen before generating these 90 masks.
It is not external preregistration or independent confirmation. The amendment
changes no masks, seeds, methods, analysis choices, or retention rules. There
will be no tuning of these choices after observing these results.

## Reporting amendment after the initial completed run

After completing and deterministically repeating the original 90 cases, an
independent audit requested an explicit paired selector-minus-oracle query-cost
summary and its nonnull case count. We added that descriptive comparison and
null-safe console printing, then repeated the complete experiment twice again.
This reporting amendment changes no sampling, seeds, methods, certificate
criteria, or case retention; it is not a preregistered extra summary.
