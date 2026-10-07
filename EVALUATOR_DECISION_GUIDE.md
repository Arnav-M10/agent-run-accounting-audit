# What can this release support?

This guide concerns inherited recorded grades on a declared released roster, not independently verified agent achievement or a population performance guarantee.

| Available evidence | Report | Decision consequence |
|---|---|---|
| All models have grades on the same declared tasks | Full-roster mean, task count, score range | Compare those recorded means; completion filtering is unnecessary for this target. |
| Completion-conditioned performance is the intended target | Predicate, eligible task IDs, mean, and coverage | The conditional mean describes that selected population. Different predicates answer different questions. |
| Eligible task sets differ between models | Separate means and, if wanted, one declared shared-task comparison | Pair matching changes the population. Different pair intersections can yield cycles; a cycle is not evidence of grader error. |
| Grade evidence is unavailable but the common roster and finite range are known | Bounds, strict-order certificates, exact ties and unresolved pairs | Withhold unsupported strict orders; do not silently assign failures. |
| Existing unavailable grades might be recovered | Pairwise recovery diagnostic and unavailable grade IDs | An optimistic minimum rules out too-small recovery counts. Actual outcomes determine success; equal weights give no unique task priority. |
| Roster identities or missing model allocation are unknown | Aggregate counts and limits of identification | Do not invent task support or model-specific orders. |
| Raw extraction or achievement has not been independently checked | Explicit verification boundary | Arithmetic tests cannot establish semantic score validity. |

## Worked recorded-grade example

Claude Fable 5 has all-run recorded mean 62.0045% on 60 released tasks, versus 67.6413% on 55 assistant-ending tasks. These describe different populations. If only the 55 grades were supplied, the declared [0,1] full-roster interval would be [62.0045%,70.3378%]. Use all 60 grades when they are available; do not substitute the assistant-conditioned mean as a full-roster estimate.

## Worked recovery example (synthetic)

Four equally weighted tasks: A has grades 1,1 plus two unavailable grades; B has four grades 0.6. A-B lies in [-0.1,0.4]. One favorable recovered A grade above 0.4 could certify A>B; recovering zero would not. A returned count of one is possible, not guaranteed. Revealing both models' grades for one task costs two grade recoveries. Pairwise counts cannot be combined into a global recovery budget.

## Use

Use `bounded_comparison.py selected.jsonl --roster roster.json` for existing support; use `recovery_diagnostics.py selected.jsonl --roster roster.json` to inspect possible recovery. The roster declares `tasks` and `models`. See RECOVERY_METHOD_PLAN.md for proof, range assumptions and overlap with established aggregation-query methods. Neither tool calls a model or grades task achievement.
