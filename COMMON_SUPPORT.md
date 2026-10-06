# Pairwise task-support audit

This extension was planned on 5 October 2026 after seeing the earlier ordering results. It is exploratory. All available pairs and all three previously examined predicates are reported, including comparisons whose direction does not change. Fixed recorded grades are used; no new inference or independent outcome verification occurs.

## Three comparisons and exact identity

Let T be the identical fully scored task roster for A and B; R_A and R_B are the task IDs passing the declared rule for each model, and I = R_A intersect R_B. Let mu_m(S) be the mean native recorded grade of model m on task set S.

- Full gap D_T = mu_A(T) - mu_B(T).
- Separately filtered gap D_F = mu_A(R_A) - mu_B(R_B).
- Common-support gap D_I = mu_A(I) - mu_B(I).

D_F - D_T = (D_I - D_T) + (D_F - D_I).

The first component is selection of a common task subset; the second compares unequal task supports. These are accounting components, not causal effects. Native and filtered grades on exactly the same task set are identical. Persistence means the common-subset ordering differs from the FULL-roster ordering, not that changing the score definition changes outcomes on fixed tasks.

## Complete fixed-release results

| Predicate | Pairs | Separate-support reversals | Existing reversals persisting on common support | All common-support reversals | Common task range |
|---|---:|---:|---:|---:|---:|
| Assistant ending | 66 | 8 | 4 of 8 | 7 | 42–60 |
| Native stop | 66 | 17 | 17 of 17 | 24 | 20–53 |
| Exporter completed | 45 | 2 | 1 of 2 | 2 | 50–58 |

No intersection is empty and no reversal becomes a tie. Exporter comparisons cover the ten models with available status, not the two models whose status remains unknown. All 720 grades remain in the native comparison. Full results include common task IDs, both selected counts, exclusive counts, all three gaps and both components.

A concrete example (Kimi K3 minus Qwen3.8 Max, assistant rule): full 60-task gap -1.6805 percentage points; separately filtered gap +4.4821; common 45-task gap -5.1964. Components: common-subset selection -3.5159 points, unequal-support +9.6785 points. See machine-readable full precision for exact values; displayed values are rounded.

## Reproduction

```sh
python3 common_support_audit.py run_accounting/wildclaw_released_pairs.jsonl --field last_original_role --value '"assistant"'
python3 common_support_audit.py run_accounting/wildclaw_released_pairs.jsonl --field native_stop_reason --value '"stop"'
python3 demo_common_support.py
python3 -m unittest test_common_support_audit.py
```

The demonstration restricts exporter-status analysis to the ten fully status-covered models and labels that restriction. The generic command itself does not silently exclude models with unknown fields. Unknown/null fields remain distinct; absent fields never match. The tool requires identical task rosters, unique model-task identities, complete available grades and one finite score scale. It refuses missing grades and incomplete rosters rather than silently constructing a new baseline.

This is a descriptive diagnostic, not a new estimator or corrected leaderboard. Intersections are selected by both models' execution properties, so task matching does not recover excluded performance or remove selection bias. Some intersections contain only 20 of 60 tasks. Pair-specific intersections differ and need not yield a coherent or transitive global ranking. An intersection can introduce new reversals as well as remove existing ones; therefore all pairs are reported. No inferential intervals or causal interpretation are claimed.

Related primary work: Wei-Jung Huang, *How Many Tasks Are Enough for Agent Benchmark Decisions?* (arXiv:2607.12338v1), examines preservation of pairwise conclusions under partial task sets. This audit examines recorded completion-rule selection in two released trajectory collections, with an executable support comparison; it makes no first-method claim.

## Magnitudes and undefined comparisons

Absolute margins for separate-support reversals, on the native [0,1] scale (shown in percentage points):

| Rule | Full-roster margin range | Separately filtered margin range |
|---|---:|---:|
| Assistant ending | 0.88–5.18 | 0.46–6.69 |
| Native stop | 0.88–12.71 | 0.48–11.92 |
| Exporter completed | 0.28–2.22 | 0.54–2.85 |

These enumerate fixed-release sign changes, not statistically established differences. Full precision is in common_support_results.json. Predicate equality treats JSON numbers 1 and 1.0 as equal and distinguishes booleans, matching summarize_ledger.py. If either separately selected population is empty, its gap and reversal indicator are null and its classification is undefined_separate. Empty intersections have a null common-gap/reversal indicator. Neither is counted as an observed non-reversal. None occurs in the reported three-policy released-data analysis.
