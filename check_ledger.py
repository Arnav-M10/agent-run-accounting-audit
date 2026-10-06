"""Validate JSONL accounting metadata without assigning outcomes or filling nulls.

Standard library only. Identity fields are explicit, so this also checks slots
and released pairs whose source does not expose an execution identifier.
"""
import argparse
import collections
import json
import math
from pathlib import Path

MISSING = object()


def finite_numeric(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def categories(rows, fields):
    counts = collections.Counter()
    for row in rows:
        key = tuple(json.dumps(row[f], sort_keys=True) if f in row else None for f in fields)
        counts[key] += 1
    result = []
    for key, count in sorted(counts.items(), key=lambda item: repr(item[0])):
        result.append({"fields": {f: {"present": v is not None, **({"value": json.loads(v)} if v is not None else {})}
                                  for f, v in zip(fields, key)}, "count": count})
    return result


def read_rows(path):
    rows, issues = [], []
    def reject_constant(value):
        raise ValueError("Nonstandard JSON numeric constant: " + value)
    with Path(path).open() as handle:
        for line, text in enumerate(handle, 1):
            try:
                row = json.loads(text, parse_constant=reject_constant)
                if not isinstance(row, dict):
                    raise ValueError("JSON row is not an object")
                rows.append((line, row))
            except (ValueError, json.JSONDecodeError) as exc:
                issues.append({"line": line, "issue": "invalid_json_row", "detail": str(exc)})
    return rows, issues


def check(path, identity, reference_path=None, reference_field="observed_attempt_id", target_field="attempt_id"):
    numbered, issues = read_rows(path)
    rows = [row for _, row in numbered]
    seen = collections.defaultdict(list)
    numeric_scores = 0
    unchecked_ranges = 0
    for line, row in numbered:
        if any(field not in row or row[field] is None for field in identity):
            issues.append({"line": line, "issue": "missing_identity"})
        else:
            seen[tuple(json.dumps(row[field], sort_keys=True) for field in identity)].append(line)
        available = row.get("score_available", MISSING)
        score = row.get("native_score", MISSING)
        has_score = score is not MISSING and score is not None
        if available is not MISSING and available is not None and type(available) is not bool:
            issues.append({"line": line, "issue": "invalid_score_availability"})
        if available is True and not has_score:
            issues.append({"line": line, "issue": "available_without_score"})
        if available is False and has_score:
            issues.append({"line": line, "issue": "unavailable_with_score"})
        if has_score:
            if not finite_numeric(score):
                issues.append({"line": line, "issue": "invalid_score"})
                continue
            numeric_scores += 1
            scale = row.get("score_scale")
            if scale is None:
                unchecked_ranges += 1
            elif (not isinstance(scale, list) or len(scale) != 2 or
                  any(not finite_numeric(bound) for bound in scale) or scale[0] > scale[1]):
                issues.append({"line": line, "issue": "invalid_score_scale"})
            elif not scale[0] <= score <= scale[1]:
                issues.append({"line": line, "issue": "score_out_of_range"})
    duplicates = [{"identity": {f: json.loads(v) for f, v in zip(identity, key)}, "lines": lines}
                  for key, lines in seen.items() if len(lines) > 1]
    reference = None
    if reference_path:
        targets, target_issues = read_rows(reference_path)
        target_counts = collections.Counter(json.dumps(row[target_field], sort_keys=True) for _, row in targets
                                            if row.get(target_field) is not None)
        if target_issues:
            issues.append({"issue": "invalid_reference_ledger", "rows": len(target_issues)})
        ambiguous = sum(count > 1 for count in target_counts.values())
        if ambiguous:
            issues.append({"issue": "ambiguous_reference_targets", "identities": ambiguous})
        linked = 0
        for line, row in numbered:
            value = row.get(reference_field)
            if value is not None:
                linked += 1
                if json.dumps(value, sort_keys=True) not in target_counts:
                    issues.append({"line": line, "issue": "unresolved_reference", "field": reference_field})
        reference = {"field": reference_field, "target_field": target_field, "linked_rows": linked,
                     "unlinked_categories": categories([r for r in rows if r.get(reference_field) is None], [reference_field])}
    issue_counts = dict(collections.Counter(issue["issue"] for issue in issues))
    if duplicates:
        issue_counts["duplicate_identity"] = len(duplicates)
    return {"ledger": str(path), "rows": len(rows), "identity_fields": identity,
            "valid": not issues and not duplicates, "issue_counts": issue_counts,
            "issue_examples": issues[:10], "duplicate_identity_examples": duplicates[:10],
            "numeric_scores": numeric_scores, "scores_without_range_evidence": unchecked_ranges,
            "categories": {f: categories(rows, [f]) for f in
                           ("retention", "score_available", "execution_status", "last_original_role", "native_stop_reason", "coverage")},
            "role_status_grade_availability": categories(rows, ["last_original_role", "execution_status", "score_available"]),
            "reference_check": reference}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--identity", required=True, help="Comma-separated identity fields; never inferred")
    parser.add_argument("--reference-ledger", type=Path)
    parser.add_argument("--reference-field", default="observed_attempt_id")
    parser.add_argument("--target-field", default="attempt_id")
    args = parser.parse_args()
    identity = args.identity.split(",")
    if any(not field for field in identity) or len(identity) != len(set(identity)):
        parser.error("identity fields must be nonempty and distinct")
    result = check(args.ledger, identity, args.reference_ledger, args.reference_field, args.target_field)
    print(json.dumps(result, indent=2, allow_nan=False))
    raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
