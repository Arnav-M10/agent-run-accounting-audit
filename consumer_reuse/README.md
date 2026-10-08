# Actual retained-corpus reuse: Messier

A pinned public consumer imports retained CMU MathHay/Search/MCPBench Parquets, not removal files. Its frontier implementation first computes observed-trial task/agent means; it then takes the best agent per task. Our replay concerns the former reduction, not published frontier or IRT values. It introduces no new terminal filter. Source functions and consolidation are pinned in source_manifest.json.

The released consumer has 5,315 trial records whose source-reward multisets match the retained CMU ledger across all1,465 task/model groups. There are also5,394 MCP verifier rows. Consumer trials are densely renumbered:247 original pass keys are absent and46 naively joined rewards differ. Do not claim pass/event identity. Binary MCP trial results use reward>=5 and six verifier dimensions; they are not original continuous means. Historical paper-producing revisions are unknown.

All15 search model/domain cells are reported. On the same69 supported V3.2/BrowseComp tasks, observed-trial task means average33.4541%, versus25% over all four recorded grades. Both omit zero-retained groups; this is not the original pooled-run contrast or full planned-task score. Mind2Web is explicitly a negative-control extension because the consumer does not ingest it. No incorrect published estimate or adoption of our tools is established.

## Reproduce

Acquire source metadata to a private path with `python acquire_consumer.py --output /private/tmp/messier_cmu_metadata.jsonl`. It streams the pinned593.5MB public file, verifies its full checksum/size, and retains only grade/identity fields (no questions/messages). Then run `python check_consumer.py --consumer /private/tmp/messier_cmu_metadata.jsonl --ledger ../run_accounting/cmu_attempts.jsonl --out /private/tmp/consumer_replay`. Both scripts use standard-library Python; acquisition also requires curl and internet. No inference. Raw/source row data are excluded from this public package; only own scripts, counts, replay table and pins are distributed.

Primary sources: [Messier paper](https://arxiv.org/html/2607.25891v2), [pinned source](https://github.com/Andromede-AI/messier/tree/2cf0d31ba6ee8e04714dc6c782c971f1b1a49b53), [pinned consumer data](https://huggingface.co/datasets/Andromede-AI/messier/tree/42e03cf072039e1428ad1dc970711035cfd24a5e).
