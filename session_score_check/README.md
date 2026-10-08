# Actual session-score population check

Read all9 shards of public Exgentic/agent-llm-traces-v2 at4b8ad4ab198438e5a170f9171c19c6a2cf7c1814:10,056 unique session IDs (card states10,057), no session sampling. Three directed configurations each have100 available binary grades. Reviewed source completed mapping excludes error/cancelled/unknown. Solo/DeepSeek28/100 versus28/38; Solo/Kimi55/100 versus55/97; ReAct/DeepSeek66/100 versus66/96. Every excluded grade is known zero. Execution success status is not issue-resolution success.

All six means, support counts, steps and costs agree with separate historical aggregate columns. The latter contains no run ID/session roster/generating commit; matching configuration and timestamps support association, not a proven generating join. V2 lacks top-level benchmark task IDs and drops sessions without surviving chat spans. Claude/DeepSeek has99 rows versus historical100, so historical rank reversals remain unverified. The inspected full traces-v2 endpoint is gated; no task-matched capability claim or corrected leaderboard score. These three checks are directed corroboration, not representative sampling.

## Replay

Download each `data/train/FILENAME` in source_shards.json from `https://huggingface.co/datasets/Exgentic/agent-llm-traces-v2/resolve/4b8ad4ab198438e5a170f9171c19c6a2cf7c1814/` to a private directory. Then `python replay.py --root PRIVATE_SHARD_DIRECTORY`; requires PyArrow. Each size/hash is checked before reading nine named metadata columns. No messages are emitted or republished, no paid APIs. Source card has no declared license; shard files/session rows stay outside public package. Distributed contents are own replay code, source checksums and run-level aggregate summaries only.

The historical source review pin8af99b17c7b5c6a32f7578ff3a7c9e3d0f389fa5 defines numeric-score and execution-completed aggregation; it is not established as generating commit. See ../aggregate_score_check/README.md for original definitions and all150 aggregate rows, which remain a separate evidence tier.
