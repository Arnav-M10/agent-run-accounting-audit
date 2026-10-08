# Frozen analysis plan

This local plan was frozen before the new frontier score calculations, after inspecting the existing CMU audit and consumer mean replay. It is outcome-informed follow-up work, not preregistration or blind validation. The analysis uses both imported search domains (BrowseComp and WebVoyager), all five CMU models, and every task declared by the CMU search-slot ledger in those domains. Mind2Web is excluded because Messier does not import it. No model, task, or domain is selected by its result.

The source-defined reduction is observed-trial mean per task/agent, maximum over eligible agents per task, then unweighted mean over tasks within benchmark. We reproduce the terminal all-five-model reduction on the imported CMU subpopulation; this is a source-specific reduction sensitivity, not reproduction of the published full Messier frontier, its quarterly chronology, or IRT. Extracted consumer metadata omits model dates and agent IDs. The builder creates one general-agentbench agent per model, so model groups reproduce that subpopulation at a cutoff when all five are eligible.

Independently verify unique source attempt and slot keys, consumer trial keys, and exact retained reward multisets per domain/task/model. Do not join consumer dense trial IDs to original pass IDs. Verify that search results map to source_reward == 1.

For the retained-input reduction, follow the actual source rule: absent task/model groups provide no candidate. Report absent groups explicitly; do not assign them zero. For the comparison, average all four recorded CMU pass grades per task/model, preserving removed grades. An unreleased grade remains unknown in [0,1]; enumerate endpoint bounds for the resulting frontier. Both reductions use the same declared task population. If any task lacks every retained agent, no point estimate is reported for that task and bounded task support is used.

Report the complete declared task population and a separate complete-retained-support subset (tasks with at least one retained trial for every model), to expose any support change. Summarize each model/domain group coverage, retained/source attempt counts, and incomplete four-pass coverage. Report maximum-model ties and frontier changes without declaring historical publication error or causal downstream adoption.

Only own code, aggregate results, provenance hashes, and documentation are public outputs. Raw consumer/source rows remain private. Standard-library computation only, no inference, API calls, or dependency installation.
