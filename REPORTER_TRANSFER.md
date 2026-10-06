# Apply the same reporter to both releases

This demonstration checks internal arithmetic portability across two existing corpora, not independent adoption or general validation. The generic summarize_ledger.py is used without modification or a corpus-specific aggregation branch. Corpus adapters still establish native grade and row semantics.

## CMU: twelve additional summaries

```sh
python3 summarize_ledger.py run_accounting/cmu_attempts.jsonl --group-by benchmark --include 'retention="retained"' --missing-grade error
python3 summarize_ledger.py run_accounting/cmu_attempts.jsonl --group-by benchmark --missing-grade error
python3 demo_cmu_reporting.py
```

These commands reproduce six retained means and six all-released recorded-grade means. The demonstration checks each count and mean against audit_results.json. Recorded positive grades in excluded records are preserved. This is not the operational exclusion-zero policy used in the manuscript's all-initiated columns.

The ledger has 8,653 retained and 9,769 released records. There are also 329 documented earliest exclusions without row IDs. The generic reporter does not fabricate those rows or include them in a released-record denominator. Use documented aggregate accounting separately when the estimand includes these initiated attempts.

Illustrative native-scale summaries:

| Benchmark | Retained recorded mean (n) | All-released recorded mean (n) |
|---|---:|---:|
| MCP (0–10) | 3.167075 (899) | 3.105579 (956) |
| SWE (0–1) | 0.214190 (747) | 0.185061 (897) |

Full precision for all six benchmarks appears in cmu_reporting_example.json. Missing earliest rows explain why these denominators differ from the documented 1,040 MCP and 998 SWE attempts.

## A concrete misuse is rejected

```sh
python3 summarize_ledger.py run_accounting/cmu_attempts.jsonl --missing-grade error
```

This tries to pool six benchmark scales in one source group; it fails with `mixed declared score scales`. MCP's native [0,10] scale cannot be silently averaged with the others' [0,1] scales. Grouping by benchmark permits each mean on its own declared scale. This guard does not establish that equal-scale benchmarks measure the same construct; the caller must still declare meaningful groups.

## Scope

Together with demo_summarize_ledger.py, 58 summaries match corpus adapters: twelve CMU benchmark/population means and 46 WildClawBench model/policy means. This verifies transfer within the two studied releases and a concrete scale-mixing guard. It does not establish external usability, validated task achievement, semantic correctness of arbitrary user ledgers, or a generally validated reporting standard. Run check_ledger.py with appropriate identity fields before reporting; the summarizer alone does not detect duplicate identities.
