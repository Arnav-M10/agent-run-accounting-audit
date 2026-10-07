# Decision consequences of completion filtering

Two exploratory extensions use only the supplied metadata and inherited recorded grades. No inference or new grading occurs.

## Coverage-preserving reference

Run `python3 mask_reference_audit.py`. MASK_REFERENCE_PLAN.txt records the design, timing and an outcome-informed metric amendment. Within each of six released task categories, jointly permute the full vector of model eligibility. Grades and task labels stay fixed. Every draw preserves per-model category counts, pairwise overlaps and global support, which the code asserts. Seed 20261007 and 1,999 draws are fixed; all three existing rules and all planned metrics are reported.

The reference asks what happens when the same selection geometry is assigned to different tasks within category. It does not establish causal effects or task exchangeability: categories contain heterogeneous difficulty and tool requirements. This exploratory post-inspection analysis reports descriptive quantiles and exceedance counts, not confirmatory p-values. Cycles need not be exceptional even when comparison displacement is large. No sampling prevalence or population superiority is inferred.

## Bounded comparisons when omitted grades are unavailable

Run `python3 bounded_comparison.py`. Given a known full roster N, k selected grades with sum S, and declared grade range [l,u], the sharp full-roster mean interval is [(S+(N-k)l)/N, (S+(N-k)u)/N]. Pair gap bounds subtract the other model's opposite endpoint. Certify A>B only if the lower gap is strictly positive; otherwise the ordering is unresolved under these assumptions. These are deterministic partial-identification bounds, not confidence intervals or a newly invented estimator. Sharpness allows each omitted model-task grade to vary independently; no structural or monotonicity restriction is imposed.

WildClawBench actually supplies all grades. The demonstration deliberately masks grades under each existing completion rule, then uses the held-out full-roster recorded grades to check certificates. This simulates a downstream release containing only eligible records; it is unnecessary when the original full grades are available. Certified pairs: assistant 35/66, native stop 1/66, exporter 26/45. Unresolved: 31,65,19 respectively. Incorrect certificates against held-out recorded means: zero for all, as implied by valid bounded grades. Naive conditional-mean orders reverse 8,17,2 corresponding full-roster orders. This is a coverage/certification demonstration, not validation of native outcomes, deployment performance or causality. No inference of significance is made, and all masks were chosen before this extension.

CMU search oracle illustration: 295 groups have an observed success; 241 incomplete groups have no observed success; 459 fully retained groups have no successful recorded pass. Assuming retained grades correctly describe success and excluded-pass outcomes are otherwise unrestricted, the scheduled-group oracle fraction is bounded by 295/995 to 536/995 (29.65%–53.87%). Exclusion-zero takes the lower endpoint. This is conditional on the retained-grade assumption and documented grid, not recovered achievement. Do not infer individual model attribution for the 329 aggregate-only removals outside the reconstructed search grid.

The useful decision is whether a comparison is established by the available grades on a declared roster or depends on an exclusion policy. Use all recorded grades when available; show conditional populations separately. If omitted grades are absent, report the bounds and unresolved comparisons rather than silently treating absence as zero.
