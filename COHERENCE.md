# Can matched pairwise comparisons form a leaderboard?

This exploratory follow-up was recorded in COHERENCE_PLAN.txt on 6 October 2026 after the prior support results. It uses the same fixed grades and three predicates, with all triples reported. No new inference or grading occurs.

For models A and B, an edge A -> B means A's recorded mean exceeds B's on their pair-specific eligible task intersection, using the existing 1e-12 native-scale numerical tie tolerance. A directed triple A -> B -> C -> A certifies that these strict relations cannot all be represented by a single scalar order. The three edges can use different tasks. This is support-dependent non-transitivity, not inconsistent grading or a corrected measure of ability.

| Rule | Models | Triples | Cyclic triples | Global eligible tasks |
|---|---:|---:|---:|---:|
| Assistant ending | 12 | 220 | 4 | 31/60 |
| Native stop | 12 | 220 | 3 | 17/60 |
| Exporter completed | 10 | 120 | 0 | 37/60 |

No edge is tied or undefined in these data. The counts enumerate overlapping triples, not independent events or prevalence estimates. Full-roster and separately filtered scalar controls have zero cycles, as mathematically expected. One all-model eligible intersection supports scalar means on a common population, but selects just 31, 17, or 37 tasks; it does not recover full-roster ability.

All seven cycles appear in coherence_results.json with every edge's exact gap and task IDs. One assistant example is Grok 4.5 -> Muse Spark 1.1 -> Qwen3.8 Max -> Grok 4.5: gaps 6.0586, 1.4669 and 1.7290 percentage points on 51, 49 and 48 tasks. This example illustrates the mechanism; every triple was enumerated without selecting by margin. Across assistant cycles, edge margins range 0.2747–6.4009 points; native-stop cycle edges span 0.6296–4.2505. These are observed signs, not statistically established preferences. A zero-cycle result does not imply equal task support or general ranking validity.

Related work: Yi Xu, Laura Ruis, Tim Rocktaschel and Robert Kirk, Investigating Non-Transitivity in LLM-as-a-Judge, arXiv:2502.14074v3 (2025), documents non-transitive judge preferences. Here pair-specific completion-conditioned populations differ while the inherited task grades remain fixed. No first-method claim is made.

Run python3 coherence_audit.py to regenerate all three rules, or python3 coherence_audit.py run_accounting/wildclaw_released_pairs.jsonl --field last_original_role --value '"assistant"' for a declared predicate. The generic command does not silently restrict unknown statuses; the built-in exporter demonstration explicitly uses the ten status-covered models. Unit tests include an exact three-task cycle with empty global support, coherent identical supports and undefined edges distinct from ties.
