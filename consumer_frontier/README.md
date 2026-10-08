# CMU-derived Messier frontier reduction sensitivity

This outcome-informed local extension evaluates the pinned consumer's actual final reduction on its **CMU-derived imported search component**: observed-trial task/agent mean, best eligible agent per task, then unweighted benchmark task mean. It includes both imported search domains and all five CMU models. The frozen local plan is [PLAN.md](PLAN.md); it is not preregistration or blind validation.

The result changes after the source-defined maximum over agents, so the effect is not confined to the previously reported individual-model means. On the complete declared task populations:

| Domain | Tasks | Retained-input terminal reduction | Four-pass grade reduction | Difference, percentage points |
|---|---:|---:|---:|---:|
| BrowseComp | 124 | 21.3038% | 16.5323–16.7339% | +4.5699–4.7715 |
| WebVoyager | 65 | 73.2051% | 72.6923% | +0.5128 |

Every one of the 189 imported search tasks has a retained candidate. Their task population is identical on both sides of each comparison. The complete search ledger has 199 tasks; the remaining 10 are Mind2Web, which the consumer does not import.

Missing retained model/task groups are **absent candidates**, as in the consumer's observed-support rule. They are not numerical zeroes: BrowseComp has 45 absent R1 and 55 absent V3.2 groups; WebVoyager has one absent Flash and one absent Qwen3-235B group. Removed runs with known grades remain in the four-pass comparison. The one unreleased R1/BrowseComp grade remains unknown in [0,1]; monotonicity of the task maximum yields the exact overall endpoints, 41/248 and 83/496. The retained-input value is 317/1488, so the exact difference range is [17/372, 71/1488]. No missing grade is fabricated.

The source reduction can mask model-specific changes. Twenty BrowseComp task maxima definitely change and one additional task can change depending on the unreleased grade; only two WebVoyager task maxima change. The maximum task-level increase is 75 percentage points on BrowseComp and 16.6667 on WebVoyager. We report the smaller WebVoyager effect alongside BrowseComp and do not choose the domain by effect size.

For descriptive support sensitivity, the subset with retained observations for all five models has **42 BrowseComp** and **63 WebVoyager** tasks. On these identical subsets the retained/four-pass values are 32.3413%/23.2143% (+9.1270 points) and 73.9418%/73.4127% (+0.5291 points), respectively. These are distinct populations and must not be substituted for the all-declared-task results. They also differ from a subset selected solely for complete recorded four-pass grades.

## Scope and verification

This is a reduction replay and denominator sensitivity, not a reconstruction of the published Messier frontier, model-release chronology, full multi-corpus agent population, or IRT. The pinned builder maps each fixed source-model label deterministically to a general-agentbench agent; the local terminal reduction treats all five source models as eligible. The private extracted metadata omits agent IDs and model dates, so we do not independently verify date eligibility or claim a historical generating revision. The effect concerns this identifiable CMU imported component; it does not establish a numerical error in Messier's published results.

The checker independently verifies unique source/slot/consumer keys, source attempt identities against declared slots, exact retained-grade multisets for all search task/model groups, binary consumer grade mapping, and every pinned source-file hash. It deliberately does not equate dense consumer trial numbers with original pass identities. All 3,092 imported search consumer trials across 843 observed task/model groups match retained source grade multisets. `coverage.csv` reports every model/domain cell, including absent groups and known removed/unknown grades; `results.json` stores exact fractions, ties, bounds, coverage, and provenance hashes. An independent checker derived the aggregate frontier values from the source ledger and slots without importing this extension's code.

## Reproduce

Acquire private metadata using the adjacent consumer-reuse acquisition script and its pinned full-data checksum. Keep extracted metadata and source/consumer rows private. With the pinned source checkout already acquired, run from the project root:

```sh
python3 submission/reproducibility/consumer_frontier/check_frontier.py \
  --consumer /private/tmp/aes_messier_verified_metadata.jsonl \
  --ledger submission/reproducibility/run_accounting/cmu_attempts.jsonl \
  --slots submission/reproducibility/run_accounting/cmu_search_slots.jsonl \
  --manifest submission/reproducibility/consumer_reuse/source_manifest.json \
  --source-root /private/tmp/aes_consumer_sources/messier \
  --out submission/reproducibility/consumer_frontier
```

The code uses standard-library Python and existing recorded grades only. No inference, API calls, downloads, or dependency installation occurs in the replay. Public outputs contain own code, aggregate results, documentation, and hashes; no raw consumer/source rows.

Pins and primary sources are in the adjacent [source manifest](../consumer_reuse/source_manifest.json): consumer code `2cf0d31ba6ee8e04714dc6c782c971f1b1a49b53`, consumer data `42e03cf072039e1428ad1dc970711035cfd24a5e`, CMU source `88e2af82c116a9a57f29be6f21b9924da081c2bd`. Historical paper-producing revision is unknown.
