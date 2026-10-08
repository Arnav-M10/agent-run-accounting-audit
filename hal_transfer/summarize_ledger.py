#!/usr/bin/env python3
"""Report explicit populations and recorded scores from a JSONL ledger (stdlib only)."""
import argparse
import json
import math
from pathlib import Path


def numeric(value):
    try:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    except OverflowError:
        return False


def parse_rule(text):
    field, separator, literal = text.partition('=')
    if not separator or not field or any(c in field for c in '=!<>'):
        raise argparse.ArgumentTypeError('Use FIELD=JSON_VALUE; only exact equality is supported')
    try:
        value = json.loads(literal, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    except (ValueError, json.JSONDecodeError) as exc:
        raise argparse.ArgumentTypeError('Rule value must be valid finite JSON') from exc
    if isinstance(value, (int, float)) and not isinstance(value, bool) and not numeric(value):
        raise argparse.ArgumentTypeError('Rule value must be finite')
    if isinstance(value, (list, dict)):
        raise argparse.ArgumentTypeError('Equality rule values must be JSON scalars')
    return field, value


def equal(left, right):
    # JSON booleans must not match numeric 0 or 1.
    return (type(left) is type(right) or (numeric(left) and numeric(right))) and left == right


def summarize(path, group_fields, rules, missing_grade, score_field='native_score', scale_field='score_scale'):
    groups = {}
    observed = set()
    row_count = 0
    with Path(path).open(encoding='utf-8') as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f'Line {line_number}: blank line is not a ledger record')
            try:
                row = json.loads(line, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
            except ValueError as exc:
                raise ValueError(f'Line {line_number}: invalid JSON') from exc
            if not isinstance(row, dict):
                raise ValueError(f'Line {line_number}: record must be an object')
            row_count += 1
            observed.update(row)
            score = row.get(score_field)
            scale = row.get(scale_field)
            if score is not None and not numeric(score):
                raise ValueError(f'Line {line_number}: score must be finite numeric or null')
            if scale is not None:
                if not isinstance(scale, list) or len(scale) != 2 or not all(numeric(v) for v in scale) or scale[0] >= scale[1]:
                    raise ValueError(f'Line {line_number}: scale must be [finite minimum, finite maximum]')
            if score is not None and (scale is None or not scale[0] <= score <= scale[1]):
                raise ValueError(f'Line {line_number}: scored record needs a declared scale containing its score')
            values = [{'field': f, 'present': f in row, **({'value': row[f]} if f in row else {})} for f in group_fields]
            key = json.dumps(values, sort_keys=True, allow_nan=False)
            group = groups.setdefault(key, {'group': values, 'source_population_count': 0, 'population_count': 0,
                'excluded_count': 0, 'known_ineligible_count': 0, 'unknown_eligibility_count': 0,
                'inclusion_rule_counts': [{'field': field, 'value': value, 'matched_count': 0,
                    'known_mismatch_count': 0, 'null_unknown_count': 0, 'absent_unknown_count': 0}
                    for field, value in rules],
                'scored_count': 0, 'unknown_score_count': 0,
                'null_score_count': 0, 'absent_score_count': 0, 'undeclared_scale_count': 0,
                '_scales': set(), '_scores': []})
            group['source_population_count'] += 1
            # Check scales across the entire source group, including excluded rows.
            if scale is not None:
                group['_scales'].add(tuple(scale))
            if len(group['_scales']) > 1:
                raise ValueError(f'Line {line_number}: mixed declared score scales within group {values}')
            rule_states = []
            for (field, value), counts in zip(rules, group['inclusion_rule_counts']):
                if field not in row:
                    state = 'absent_unknown'
                elif row[field] is None and value is not None:
                    state = 'null_unknown'
                else:
                    state = 'matched' if equal(row[field], value) else 'known_mismatch'
                counts[state + '_count'] += 1
                rule_states.append(state)
            # A known false predicate decides an AND rule even if another is unknown.
            known_ineligible = 'known_mismatch' in rule_states
            unknown_eligibility = not known_ineligible and any(
                state in ('null_unknown', 'absent_unknown') for state in rule_states)
            included = not known_ineligible and not unknown_eligibility
            if not included:
                group['excluded_count'] += 1
                group['known_ineligible_count' if known_ineligible else 'unknown_eligibility_count'] += 1
                continue
            group['population_count'] += 1
            group['undeclared_scale_count'] += scale is None
            if score is None:
                group['unknown_score_count'] += 1
                group['null_score_count' if score_field in row else 'absent_score_count'] += 1
                if missing_grade == 'error':
                    raise ValueError(f'Line {line_number}: included record has an unknown score (policy=error)')
            else:
                group['scored_count'] += 1
                group['_scores'].append(score)
    for field in (score_field, scale_field):
        if field not in observed:
            raise ValueError(f'Reporting field {field!r} is absent from every record; declare unknown values explicitly')
    for field, _ in rules:
        if field not in observed:
            raise ValueError(f'Inclusion field {field!r} is absent from every record')
    for field in group_fields:
        if field not in observed:
            raise ValueError(f'Grouping field {field!r} is absent from every record')
    result = []
    for key in sorted(groups):
        group = groups[key]
        scores = group.pop('_scores')
        scales = group.pop('_scales')
        group['declared_scale'] = list(next(iter(scales))) if scales else None
        unknown_count = group['null_score_count'] + group['absent_score_count']
        if missing_grade == 'zero' and unknown_count and (group['declared_scale'] is None or not group['declared_scale'][0] <= 0 <= group['declared_scale'][1]):
            raise ValueError('Zero assignment requires a declared scale containing zero')
        denominator = group['population_count'] if missing_grade == 'zero' else group['scored_count']
        group['mean_denominator'] = denominator
        group['recorded_score_mean'] = math.fsum(scores) / len(scores) if scores else None
        group['policy_score_mean'] = math.fsum(scores) / denominator if denominator else None
        group['score_coverage'] = group['scored_count'] / group['population_count'] if group['population_count'] else None
        group['labels'] = {'conditional_population': bool(rules),
            'uses_scored_denominator': missing_grade == 'exclude',
            'unknown_grades_assigned_zero': missing_grade == 'zero'}
        result.append(group)
    return {'ledger': str(Path(path).resolve()), 'source_record_count': row_count,
        'group_fields': group_fields, 'score_field': score_field, 'scale_field': scale_field,
        'inclusion_rules': [{'field': field, 'operator': 'eq', 'value': value, 'requires_field_presence': True} for field, value in rules],
        'missing_grade_policy': missing_grade, 'groups': result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ledger', type=Path)
    parser.add_argument('--group-by', action='append', default=[], metavar='FIELD')
    parser.add_argument('--include', action='append', type=parse_rule, default=[], metavar='FIELD=JSON_VALUE', help='Repeated equality rules are ANDed; null matches explicit null only')
    parser.add_argument('--missing-grade', required=True, choices=['error', 'exclude', 'zero'])
    parser.add_argument('--score-field', default='native_score')
    parser.add_argument('--scale-field', default='score_scale')
    args = parser.parse_args()
    try:
        report = summarize(args.ledger, args.group_by, args.include, args.missing_grade, args.score_field, args.scale_field)
    except (ValueError, OSError) as exc:
        parser.exit(2, f'Error: {exc}\n')
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
