# Recovery diagnostics prototype

This standalone prototype reuses `bounded_comparison.report_selected` and its
input validation. It takes the current selected-score ledger, an explicitly
declared common task roster and model list, and a finite score range `[a,b]`.
Every task has weight `1/N`. Missing rows and explicit unavailable scores are
unavailable model-task slots; neither is assigned an outcome.

## Diagnostic

One query reveals the grade for one unavailable slot. It can reduce that
model's mean interval width, and hence each affected pair's gap interval width,
by `(b-a)/N`. This is also the greatest possible upward movement of a pair's
lower gap endpoint or downward movement of its upper gap endpoint. All slots
have identical a priori leverage under these assumptions; the report does not
rank tasks by expected information or cost.

Counts are pairwise grade-query counts, not a simultaneous all-pairs budget.
A query of one model-task slot can affect several pairs, and favorable
outcomes supporting different pairwise claims may conflict. Counts must not
be summed or pooled into a global recovery guarantee. Equal leverage implies
no unique priority among unavailable slots.

For gap bounds `[L,U]`, let `w=(b-a)/N`, let `M` be the number of unavailable
slots in the two models, and retain the existing strict tolerance `TOL`. Search
integers `r` from zero through `M` for

`L + r*w > TOL` or `U - r*w < -TOL`.

The smallest such `r` is an **optimistic lower bound** for possible strict
certification. Endpoint grades favorable to either direction attain that
direction's maximum endpoint movement, so the formula characterizes possible
certification in the unconstrained independent range model. The report includes
the two directional minima and every unavailable slot for each pair. A null
minimum means neither direction can become strict within the range and missing
slots. Already certified pairs require zero queries; a complete exact tie
cannot support a strict claim. A nonzero complete gap within the strict
tolerance likewise cannot support one.

This is not a guaranteed recovery budget: adverse recovered grades can leave
the pair unresolved or yield a tie after every slot is recovered. It is not an
optimal adaptive recovery policy. The prototype does not query a model, invoke
an inference API, simulate outcomes as observations, or update a ledger.

## Scope and overlap

This is an operational diagnostic derived from existing bounded-score partial
identification and interval-certification logic, not a novel estimator. It
overlaps with worst-case information acquisition and best-case certificate
budgets. Related prior work includes Olston and Widom's
[Offering a Precision-Performance Tradeoff for Aggregation Queries over
Replicated Data](https://www.vldb.org/conf/2000/P144.pdf) (VLDB 2000), which
studies refreshing bounded data to improve aggregation precision. This
prototype's equal-weight width calculation is not claimed as a novel
algorithm. A stronger recovery policy would need explicit query costs, outcome
information, dependence constraints, or a stated probabilistic objective;
those are outside this prototype. Inferred outcomes, unequal task weights,
model-specific rosters, and grades outside the declared range must not be
silently substituted into the equal-weight calculation.

## Use and verification

Run from this directory:

```text
python recovery_diagnostics.py SELECTED_LEDGER.jsonl --roster ROSTER.json
python -m unittest test_recovery_diagnostics
```

The roster JSON contains `tasks` and `models` lists. Use `--score-range a b`
for another declared scale. Output is JSON printed to standard output, with
no file changes. Tests exhaustively enumerate small binary observed/missing
patterns, queried subsets, and query outcomes, and compare the first possible
certificate with the reported optimistic minimum. Additional tests cover
adverse outcomes, exact ties, strict tolerance, omitted/null slots, alternate
scales, and invalid selected-ledger inputs.
