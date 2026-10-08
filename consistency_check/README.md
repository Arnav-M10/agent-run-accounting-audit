# Post hoc outcome-consistency screen

Status: retain as a compact empirical extension, not a new metric, a broad latent-reliability contribution, or a causal analysis. No human study, new inference or paid API calls are required.

This plan was created after inspecting the existing oracle findings and the public metric. It is explicitly outcome-informed. All 15 model/domain cells are reported to expose the localized nature of the strongest result.

## Replay

Python standard library only, from the artifact directory:

```
python3 consistency_check/screen.py
python3 consistency_check/verify.py
```

Copy these scripts elsewhere to replay; the screen's default ledger path is relative to its packaged location. Results are results.json, groups.jsonl, and all_cells.csv. Verification exhaustively enumerates binary completions and retained-size subsets of every four-outcome vector.

## Prior metric and target

Rabanser et al., Towards a Science of AI Agent Reliability, arXiv:2602.16666v3, Table 2, defines outcome consistency as the task mean of C_K(s)=(2s/K-1)^2 using a fixed number K of repeated runs. Section 3.1 explicitly includes consistent failure. Source verified at https://arxiv.org/html/2602.16666v3 . The original paper's fixed-K protocol is not being criticized as a variable-K analysis.

Here the target is empirical consistency of the recorded scheduled four-pass vector, not the latent repeated-run success probability. Using retained k_t in place of K=4 changes the measurement. Selecting only four-retained groups changes task support. Dropping k=0 groups changes support again. A k=0 consistency is undefined and must not be assigned zero or one.

## Data reconstruction

The search ledgers contain 995 scheduled model/task groups (5 models x 199 tasks), 3,980 slots, and 3,979 grades. All available scores are binary. Retained-count distribution is k=4:722, k=3:91, k=2:29, k=1:51, k=0:102. All 709 removed recorded passes have score zero. The sole absent grade is R1/BrowseComp task44, with three recorded zeros and no retained passes. Its four-pass consistency is 1 if the absent grade is0, or0.25 if1. This creates the narrow full-roster interval; it does not justify filling the grade with0.

## Strongest same-task result

V3.2/BrowseComp has124 tasks:69 supported by at least one retained run, and55 with k=0. The supported69 consist of14 complete groups,20 k=3,9 k=2,26 k=1. All their four scheduled grades are available.

On exactly these69 tasks:

| Summary | Value |
|---|---:|
| Full four-pass C | 0.7427536232 |
| Uniform subsets of actual retained size, exact expectation | 0.8007246377 |
| Actual retained variable-k C | 0.8844605475 |

Thus actual available-run consistency rises14.17069243 percentage points. The exact subset-size reference accounts for5.79710145 points, and actual retained subsets differ from the reference by8.37359098 points. This is an arithmetic contrast for these observed vectors, not a causal decomposition. No donor tasks, IID run assumption, Monte Carlo sampling, or missing-grade imputation are needed.

The full124-task C is0.8568548387. Its comparison with the69-task statistic mixes support and measurement. The14 complete-group C is0.875. The55 zero-retained tasks all have four recorded failure grades, so each contributes1 to full-vector consistency. Among all124 tasks,96 always fail and7 always succeed. These high consistency values must not be presented as strong success or operational reliability.

## Finite subset-size reference

For a fixed binary four-vector with s successes and p=s/4, uniformly choose any k of its four positions, without replacement. Exact hypergeometric arithmetic yields

E[C_k | vector,k] = C_4 + 4p(1-p)(4-k)/(3k).

Equivalently C_4+(1-C_4)(4-k)/(3k). This is finite-vector subset arithmetic. Under an additional IID Bernoulli model the plug-in statistic also has the familiar sample-size term E[C_k]=(2p-1)^2+4p(1-p)/k, but that model is unnecessary here and should not support any causal claim. k=1 always yields C=1. The corrected U_k=(k C_k-1)/(k-1) for k>1 removes the IID plug-in bias but changes scale and excludes singleton tasks; it does not repair outcome-dependent selection. It is not proposed as a new metric.

## All-roster summary and reversals

Full scheduled C lies in[0.8178391960,0.8185929648]; available retained C is0.8119323131 on893 tasks; complete-only C is0.7873961219 on722 tasks. Thus there is no general claim that filtering inflates consistency on the whole roster.

An ordering reversal is robust to the single absent grade: full R1 C lies in[0.8216080402,0.8253768844], above Qwen3-235B's0.8190954774; available-retained values are0.7812049062 and0.8181818182, respectively. This mixes task support and measurement and should not be described as a same-task ranking result. All model and cell summaries are in results.json/all_cells.csv.

## Sharp nonlinear missing-grade bounds

If only k retained outcomes are supplied, with s successes and m=4-k unknown binary grades, then

L=min_{j=0,...,m} (2(s+j)/4-1)^2,
U=max_{j=0,...,m} (2(s+j)/4-1)^2.

The maximum occurs at an endpoint, but the minimum is the feasible total success count nearest2 and may be interior. For instance, k=0 gives[0,1], with the minimum at two successes; assigning every missing grade zero misses that minimum. Average these independent group extrema for exact sharp task-mean bounds. This is a small convex enumeration extension of the existing audit, not a novel general partial-identification theorem.

The retained-only all995-group bounds are[0.5907035176,0.8336683417], much wider than the bound when all3,979 public grades are used. The distinction between actually missing grades and deliberately omitted available grades is essential.

## Novelty decision

The most useful addition is that retention distorts an existing repeatability statistic even on the same69 tasks, with an exact fixed-vector subset-size reference. It extends the existing mean/oracle audit to a nonlinear multi-run summary and eliminates the donor-task composition problem in the oracle thinning diagnostic. Its strengths are a concrete localized14.17-point effect, an exact5.80/8.37-point arithmetic reference, and no new experiments or paid calls.

Its weaknesses are reuse of the same anomalous V3.2/BrowseComp cell, post hoc selection, all removed grades being failures, much smaller effects elsewhere, and the fact that high consistency can mean consistent failure. This cannot transform AES into a general reliability paper or justify calling the statistic or bounds new. Retain only if framed as a compact additional empirical scope check; scrap it if the desired contribution is an independent new study or broadly validated reliability method.

The replay rejects incompatible or duplicate roster entries and records both input ledger hashes. This is a fixed-release audit, not a general estimator for arbitrary repeated-run data.
