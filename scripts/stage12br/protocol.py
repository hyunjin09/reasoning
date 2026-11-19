"""Prospective validity repair only; no scientific answer grading."""
import hashlib
from scripts.stage12br.common import ROOT, load

SELECTION_SEED = 'stage12br-validation-v1'


def select_families(rows, excluded):
    # Project to permitted metadata before ranking; never inspect outcomes.
    eligible = [{k: r[k] for k in ('item_id', 'family_id', 'answer_type')}
                for r in rows if r['item_id'] not in set(excluded)]
    assert len(eligible) == 49 and len({r['family_id'] for r in eligible}) == 49
    for r in eligible:
        r['selection_hash'] = hashlib.sha256((SELECTION_SEED + '|' + r['family_id']).encode()).hexdigest()
    ordered = sorted(eligible, key=lambda r: (r['selection_hash'], r['family_id']))
    selected = []
    for answer_type, n in [('multiple_choice', 5), ('open_ended', 7)]:
        candidates = [r for r in ordered if r['answer_type'] == answer_type]
        assert len(candidates) >= n
        selected.extend(candidates[:n])
    selected.sort(key=lambda r: (r['selection_hash'], r['family_id']))
    return [r['item_id'] for r in selected], ordered


def validity(input_valid, scoreable, cap_hit, terminal_ambiguity):
    assert all(isinstance(x, bool) for x in (input_valid, scoreable, cap_hit, terminal_ambiguity))
    assert not (terminal_ambiguity and scoreable)
    truncated = cap_hit and not scoreable
    return dict(INPUT_VALID=input_valid, SCOREABLE=scoreable,
                TRUNCATED_BEFORE_OUTCOME=truncated,
                TECHNICALLY_VALID=input_valid and scoreable and not truncated,
                cap_after_outcome=cap_hit and scoreable)


def gate(rows):
    assert set(rows) == set('ENO') and all(len(rr) == 12 for rr in rows.values())
    summaries = {a: dict(n=12, **{k: sum(r[k] for r in rr) for k in
                 ['INPUT_VALID', 'SCOREABLE', 'TRUNCATED_BEFORE_OUTCOME', 'TECHNICALLY_VALID', 'cap_after_outcome']})
                 for a, rr in rows.items()}
    passed = {a: s['INPUT_VALID'] == 12 and s['SCOREABLE'] >= 10 and s['TRUNCATED_BEFORE_OUTCOME'] <= 1
              for a, s in summaries.items()}
    decision = ('INPUT_INTEGRITY_FAIL' if any(s['INPUT_VALID'] != 12 for s in summaries.values()) else
                'VALIDITY_REPAIRED' if all(passed.values()) else 'SCOREABILITY_FAIL')
    return dict(summaries=summaries, pass_by_arm=passed, decision=decision)


def authorize_manifest(manifest, frozen=None):
    if frozen is None:
        frozen = load(ROOT / 'stage12br_validation_manifest.json')
    assert manifest['frozen'] and manifest['phase'] == 'validation'
    assert manifest['config_sha256'] == frozen['config_sha256']
    expected = {t['task_id']: t for t in frozen['tasks']}
    assert len(expected) == 36
    tasks = manifest['rows']
    assert 0 < len(tasks) <= 18 and len({t['task_id'] for t in tasks}) == len(tasks)
    assert all(t == expected.get(t['task_id']) for t in tasks), 'Only exact fresh frozen E/N/O tasks authorized'
