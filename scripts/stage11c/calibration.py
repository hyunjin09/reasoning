"""Completion-only common-cap validation on the frozen12 technical cases."""
from scripts.stage11c.common import ROOT, ARMS, load, save, sha, now
from scripts.stage11c.protocol import choose_cap
from scripts.stage11c.calibration_attempts import collect


def main():
    manifest_path = ROOT/'calibration_tasks.json'
    manifest, tasks, models, valid, attempts = collect()
    assert len(tasks) == 48 and len({r['item_id'] for r in tasks.values()}) == 12
    records = [v['receipt'] for v in valid.values()]
    missing = [ident for ident in tasks if ident not in valid]
    if missing:
        print('INCOMPLETE', len(records), '/48; unresolved', missing)
        return
    counts, summaries, pathological = {}, {}, []
    for cap in [4096, 8192]:
        counts[cap], summaries[cap] = [], {}
        for arm in ARMS:
            rows = [r for r in records if r['cap'] == cap and r['arm'] == arm]
            assert len(rows) == 12
            hits = sum(r['at_length_cap'] for r in rows)
            structural_failures = sum(not r['structural_complete'] for r in rows)
            counts[cap].append(hits)
            summaries[cap][arm] = dict(n=12, cap_hits=hits, cap_rate=hits/12,
                structural_failures=structural_failures, normal_eos=sum(r['normal_eos'] for r in rows),
                generated_tokens=sum(r['tokens'] for r in rows),
                generation_seconds=sum(r['batch_seconds'] for r in rows))
            if structural_failures > 3 and cap not in pathological:
                pathological.append(cap)
    choice = choose_cap(counts, pathological_caps=pathological)
    save(ROOT/'stage11c_cap_validation.json', dict(at=now(), frozen=True,
        status='COMPLETE', **choice, counts=summaries, pathological_caps=pathological,
        candidate_caps=[4096, 8192], technical_cases=12, valid_generations=48,
        calibration_manifest_sha256=sha(manifest_path),
        attempts=attempts, valid_receipt_paths={k: v['path'] for k, v in valid.items()},
        criterion='Smallest common cap with <10% cap hits in each arm and <=25% structural failures.',
        model_accuracy_not_used=True, primary_outcomes_opened=False,
        first_primary_gate='First16 matched families: stop before further native/oracle if either arm has >4 cap hits.'))
    print('CALIBRATION_FROZEN', choice, summaries)


if __name__ == '__main__':
    main()
