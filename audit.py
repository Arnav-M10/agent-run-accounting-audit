"""Reproduce the run-denominator audit from local CMU trajectory files.

Requires only Python's standard library. Run: python3 audit.py
The script reads data/ and writes audit_results.json; it never calls an API.
"""

from collections import Counter, defaultdict
import json
from pathlib import Path
import random


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
BENCHMARKS = (
    "tau2bench", "swebench", "terminalbench", "mathhay", "search", "mcpbench"
)
# Published original counts and first-round removals in CLEANING_SUMMARY.md.
ORIGINAL = {
    "tau2bench": 1000, "swebench": 998, "terminalbench": 1580,
    "mathhay": 1500, "search": 3980, "mcpbench": 1040,
}
ROUND1 = {
    "tau2bench": 15, "swebench": 101, "terminalbench": 128,
    "mathhay": 0, "search": 1, "mcpbench": 84,
}


def get_meta(record, disposition):
    keys = ("id", "benchmark", "domain", "task_id", "source_model", "pass", "reward")
    item = {key: record.get(key) for key in keys}
    item["disposition"] = disposition
    item["removal_reason"] = record.get("removal_reason")
    messages = record.get("messages") or []
    item["last_role"] = messages[-1].get("role") if messages else None
    return item


records = []
for benchmark in BENCHMARKS:
    with (DATA / (benchmark + ".jsonl")).open() as handle:
        for line in handle:
            records.append(get_meta(json.loads(line), "retained"))
for name in ("removed_truncated", "removed_incomplete"):
    with (DATA / (name + ".json")).open() as handle:
        batch = json.load(handle)
    records.extend(get_meta(row, name) for row in batch)
    del batch

ids = [r["id"] for r in records]
assert len(ids) == len(set(ids)), "Duplicate record IDs"
assert len(records) == 8653 + 228 + 888, "Released record count mismatch"
assert sum(ORIGINAL.values()) == 10098
assert sum(ROUND1.values()) == 329

by_bench = defaultdict(lambda: defaultdict(list))
by_model = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
groups = defaultdict(lambda: {"retained": [], "removed": []})
for r in records:
    bench, model = r["benchmark"], r["source_model"]
    assert bench in BENCHMARKS
    assert r["pass"] in (1, 2, 3, 4)
    assert r["reward"] is not None, r["id"]
    by_bench[bench][r["disposition"]].append(r)
    by_model[bench][model][r["disposition"]].append(r)
    key = (bench, model, r["domain"], str(r["task_id"]))
    groups[key]["retained" if r["disposition"] == "retained" else "removed"].append(r)

summary = {
    "source": "Local records from cx-cmu/agent_trajectories; original and round1 counts from CLEANING_SUMMARY.md",
    "record_counts": dict(Counter(r["disposition"] for r in records)),
    "benchmark": {},
    "model_benchmark": {},
    "domain_model": {},
    "four_pass": {},
    "positive_removed": [],
    "checks": {},
}

for bench in BENCHMARKS:
    d = by_bench[bench]
    kept = d["retained"]
    known_removed = d["removed_truncated"] + d["removed_incomplete"]
    assert len(kept) + len(known_removed) + ROUND1[bench] == ORIGINAL[bench], bench
    rewards = [float(r["reward"] or 0) for r in kept]
    reward_values = sorted(set(rewards))
    if bench != "mcpbench":
        assert all(value in (0.0, 1.0) for value in reward_values), (bench, reward_values[:20])
    positive_kept = sum(value > 0 for value in rewards)
    positive_removed = [r for r in known_removed if float(r["reward"] or 0) > 0]
    summary["positive_removed"].extend({k: r[k] for k in ("id", "benchmark", "source_model", "reward", "disposition")} for r in positive_removed)
    summary["benchmark"][bench] = {
        "original_attempts": ORIGINAL[bench],
        "retained": len(kept),
        "round1_unreleased": ROUND1[bench],
        "round2_truncated": len(d["removed_truncated"]),
        "round3_incomplete": len(d["removed_incomplete"]),
        "positive_retained": positive_kept,
        "retained_reward_sum": sum(rewards),
        "retained_mean_reward": sum(rewards) / len(kept),
        "attempt_mean_reward_removed_zero": sum(rewards) / ORIGINAL[bench],
        "positive_removed_count": len(positive_removed),
        "positive_removed_reward_sum": sum(float(r["reward"]) for r in positive_removed),
        "retained_reward_values": reward_values if len(reward_values) <= 3 else "continuous",
    }

for bench in BENCHMARKS:
    summary["model_benchmark"][bench] = {}
    for model, d in sorted(by_model[bench].items()):
        kept = d["retained"]
        removed = d["removed_truncated"] + d["removed_incomplete"]
        success = sum(float(r["reward"] or 0) for r in kept)
        summary["model_benchmark"][bench][model] = {
            "retained": len(kept),
            "known_removed": len(removed),
            "round2_truncated": len(d["removed_truncated"]),
            "round3_incomplete": len(d["removed_incomplete"]),
            "retained_reward_mean": success / len(kept) if kept else None,
            "known_attempt_reward_mean_removed_zero": success / (len(kept) + len(removed)),
            "known_attempt_completion": len(kept) / (len(kept) + len(removed)),
            "positive_removed_count": sum(float(r["reward"] or 0) > 0 for r in removed),
        }

domain_model = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
for r in records:
    domain_model[(r["benchmark"], r["domain"])][r["source_model"]][r["disposition"]].append(r)
for (bench, domain), models_for_domain in sorted(domain_model.items()):
    label = bench + "/" + domain
    summary["domain_model"][label] = {}
    for model, d in sorted(models_for_domain.items()):
        kept = d["retained"]
        removed = d["removed_truncated"] + d["removed_incomplete"]
        successes = sum(float(r["reward"] or 0) for r in kept)
        summary["domain_model"][label][model] = {
            "retained": len(kept),
            "known_removed": len(removed),
            "retained_reward_sum": successes,
            "complete_mean_reward": successes / len(kept) if kept else None,
            "known_attempt_mean_reward_removed_zero": successes / (len(kept) + len(removed)),
        }

for bench in BENCHMARKS:
    subset = [(key, val) for key, val in groups.items() if key[0] == bench]
    retained_four = 0
    known_four = 0
    retained_full_group_best = []
    observed_group_best = []
    retained_pass_hist = Counter()
    known_pass_hist = Counter()
    duplicate_pass_groups = []
    for key, val in subset:
        retained = val["retained"]
        removed = val["removed"]
        retained_passes = [r["pass"] for r in retained]
        all_passes = retained_passes + [r["pass"] for r in removed]
        if len(all_passes) != len(set(all_passes)):
            duplicate_pass_groups.append(str(key))
        retained_pass_hist[len(set(retained_passes))] += 1
        known_pass_hist[len(set(all_passes))] += 1
        if len(set(retained_passes)) == 4:
            retained_four += 1
            retained_full_group_best.append(max(float(r["reward"] or 0) for r in retained))
        if len(set(all_passes)) == 4:
            known_four += 1
        if retained:
            observed_group_best.append(max(float(r["reward"] or 0) for r in retained))
        else:
            observed_group_best.append(0.0)
    assert not duplicate_pass_groups, duplicate_pass_groups[:3]
    summary["four_pass"][bench] = {
        "known_model_task_groups": len(subset),
        "four_retained_pass_groups": retained_four,
        "four_known_pass_groups": known_four,
        "retained_pass_histogram": dict(sorted(retained_pass_hist.items())),
        "known_pass_histogram": dict(sorted(known_pass_hist.items())),
        "complete_case_best_of_four_mean": sum(retained_full_group_best) / len(retained_full_group_best),
        "observed_groups_best_available_mean": sum(observed_group_best) / len(observed_group_best),
    }

summary["checks"] = {
    "removed_truncated_last_role": dict(Counter(r["last_role"] for r in records if r["disposition"] == "removed_truncated")),
    "removed_incomplete_last_role": dict(Counter(r["last_role"] for r in records if r["disposition"] == "removed_incomplete")),
    "positive_removed_count": len(summary["positive_removed"]),
}

# Search has 199 shared tasks for all five models, with four planned passes
# per model/task. The sole unreleased first-round record is R1/browsecomp/44/pass3.
search_groups = {key: val for key, val in groups.items() if key[0] == "search"}
models = sorted({key[1] for key in search_groups})
task_sets = {
    model: {(key[2], key[3]) for key in search_groups if key[1] == model}
    for model in models
}
assert len(set(map(frozenset, task_sets.values()))) == 1
shared_tasks = sorted(next(iter(task_sets.values())))
assert len(shared_tasks) == 199
assert sum(len(val["retained"]) + len(val["removed"]) for val in search_groups.values()) == 3979
missing = [(key, sorted(set((1, 2, 3, 4)) - {r["pass"] for r in val["retained"] + val["removed"]}))
           for key, val in search_groups.items() if len(val["retained"]) + len(val["removed"]) < 4]
assert missing == [(('search', 'DeepSeek-R1', 'browsecomp', '44'), [3])], missing

def search_task_stats(model, task):
    retained = search_groups[("search", model, *task)]["retained"]
    return (sum(float(r["reward"] or 0) for r in retained), len(retained))

r1, qnext = "DeepSeek-R1", "Qwen3-Next"
rng = random.Random(7)
attempt_diffs = []
complete_diffs = []
for _ in range(10000):
    sample = [shared_tasks[rng.randrange(len(shared_tasks))] for _ in shared_tasks]
    rs, rc = map(sum, zip(*(search_task_stats(r1, task) for task in sample)))
    qs, qc = map(sum, zip(*(search_task_stats(qnext, task) for task in sample)))
    attempt_diffs.append((rs - qs) / (4 * len(shared_tasks)))
    complete_diffs.append(rs / rc - qs / qc)
attempt_diffs.sort()
complete_diffs.sort()
r1_successes = sum(search_task_stats(r1, task)[0] for task in shared_tasks)
r1_retained = sum(search_task_stats(r1, task)[1] for task in shared_tasks)
qnext_successes = sum(search_task_stats(qnext, task)[0] for task in shared_tasks)
qnext_retained = sum(search_task_stats(qnext, task)[1] for task in shared_tasks)
summary["search_rank_reversal"] = {
    "shared_tasks": len(shared_tasks),
    "r1_successes": r1_successes,
    "r1_retained": r1_retained,
    "qwen_next_successes": qnext_successes,
    "qwen_next_retained": qnext_retained,
    "attempts_per_model": 4 * len(shared_tasks),
    "missing_record": {"model": missing[0][0][1], "domain": missing[0][0][2],
                       "task_id": missing[0][0][3], "pass": missing[0][1][0]},
    "attempt_difference_r1_minus_qwen_next": (r1_successes - qnext_successes) / (4 * len(shared_tasks)),
    "attempt_difference_bootstrap_95": [attempt_diffs[250], attempt_diffs[9750]],
    "complete_difference_r1_minus_qwen_next": r1_successes / r1_retained - qnext_successes / qnext_retained,
    "complete_difference_bootstrap_95": [complete_diffs[250], complete_diffs[9750]],
    "bootstrap_task_resamples": 10000,
    "bootstrap_seed": 7,
}

output = ROOT / "audit_results.json"
output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

# Reusable attempt ledger: native scores are not overwritten by a metric policy.
ledger = ROOT / "run_accounting"
ledger.mkdir(exist_ok=True)
with (ledger / "cmu_attempts.jsonl").open("w") as handle:
    for r in records:
        entry = {
            "attempt_id": r["id"],
            "benchmark": r["benchmark"], "model": r["source_model"],
            "domain": r["domain"], "task_id": str(r["task_id"]), "pass": r["pass"],
            "retention": r["disposition"], "last_original_role": r["last_role"],
            "execution_status": None, "score_available": True,
            "native_score": r["reward"],
            "score_scale": [0, 10] if r["benchmark"] == "mcpbench" else [0, 1],
            "retry_of": None, "failure_attribution": None,
            "source_revision": "88e2af82c116a9a57f29be6f21b9924da081c2bd",
        }
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
with (ledger / "cmu_search_slots.jsonl").open("w") as handle:
    for key, val in sorted(search_groups.items()):
        observed = {r["pass"]: r["id"] for r in val["retained"] + val["removed"]}
        for scheduled_pass in range(1, 5):
            handle.write(json.dumps({
                "benchmark": key[0], "model": key[1], "domain": key[2],
                "task_id": key[3], "pass": scheduled_pass,
                "observed_attempt_id": observed.get(scheduled_pass),
                "coverage": "released" if scheduled_pass in observed else "aggregate_only_removal",
            }, sort_keys=True) + "\n")
(ledger / "cmu_unreleased_counts.json").write_text(json.dumps({
    "round1_by_benchmark": ROUND1,
    "note": "329 aggregate-only removals have no released attempt IDs. The single missing search slot is identifiable; no attempt ID is invented.",
}, indent=2, sort_keys=True) + "\n")
print("Wrote", output)
print("Reconciled", len(records), "released records plus", sum(ROUND1.values()), "unreleased early removals")
print("Positive removed records:", summary["checks"]["positive_removed_count"])
for bench, d in summary["benchmark"].items():
    print(bench, d["retained"], "/", d["original_attempts"],
          "mean retained", round(d["retained_mean_reward"], 4),
          "mean attempt", round(d["attempt_mean_reward_removed_zero"], 4))
