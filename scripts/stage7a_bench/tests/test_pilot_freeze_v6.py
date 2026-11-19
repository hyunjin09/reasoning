"""The retained pilot uses the exact native worker that owns each claim."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from scripts.stage7a_bench import pilot_freeze_v6 as module
from scripts.stage7a_bench.causal_provenance_v2 import object_sha
from scripts.stage7a_bench.tests.test_pilot_selection_v2 import fixture


@pytest.fixture
def packet(monkeypatch):
    actual = Path(__file__).resolve().parents[3]
    with TemporaryDirectory(dir=actual / 'outputs/stage7a_bench_v2/audit') as temporary:
        root = Path(temporary)
        out = root / 'outputs/stage7a_bench_v2'
        monkeypatch.setattr(module, 'ROOT', root)
        monkeypatch.setattr(module, 'OUT', out)
        screen, counts, entries, decisions, selected, families = fixture()
        native = screen.pop('image_present')
        native.update(benchmark='mathvision_wild', condition='photo')
        screen['photo'] = native
        counts = {'photo':200}
        originals, candidates, provenance = {}, [], []
        owners = {name:dict(native_run_id=name, event_ids=[], review_path=name+'_reviews')
                  for name in ('old_prefix', 'shard')}
        for i, (entry, decision) in enumerate(zip(entries, decisions, strict=True)):
            run = 'old_prefix' if i % 2 == 0 else 'shard'
            entry.update(benchmark='mathvision_wild', condition='photo', native_run_id=run,
                         native_index=i, annotation_path='annotation'+str(i),
                         source_annotation=dict(claim_index=0))
            originals[i] = deepcopy(entry)
            owners[run]['event_ids'].append(entry['event_id'])
            provenance.append(dict(event_id=entry['event_id'], native_run_id=run,
                                   review_path=owners[run]['review_path']))
            path = out / 'causal_pilot/prepared_candidates' / (entry['id']+'.json')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(entry))
            candidates.append(dict(path=str(path.relative_to(root)), sha256=module.sha(path)))
            decision.update(entry_sha256=object_sha(entry), fresh_visual_retrieval_demand=True,
                            fresh_demand_review_note='Exact first source read reviewed.')
        receipt = dict(screen=screen, frozen_counts=counts, family_map=families,
            generated_event_ids=[e['event_id'] for e in entries], unit_provenance=provenance,
            artifact_sha256={})
        monkeypatch.setattr(module, 'load_completed_screen', lambda *args:deepcopy(receipt))
        monkeypatch.setattr(module, 'dependency_hashes', lambda:{})
        def recompile(run, manifest, index, review_path, *args):
            assert run == originals[index]['native_run_id']
            assert review_path == owners[run]['review_path']
            return deepcopy(originals[index])
        monkeypatch.setattr(module, 'load_native_claim', recompile)
        monkeypatch.setattr(module, 'load_reviewed_controls', lambda e:({}, {'status':'UNAVAILABLE'}))
        monkeypatch.setattr(module, 'load_prior_controls', lambda e:({}, {'status':'UNAVAILABLE'}))
        request = dict(status='REVIEWED_PILOT_SELECTION_REQUEST', benchmark='mathvision_wild',
            causal_or_passive_scores_used=False, selection_review_note='Full pool reviewed before scoring.',
            bindings={'photo':dict(manifest='manifest', runs=list(owners.values()))},
            candidates=candidates, eligibility_decisions=decisions, selected_ids=selected,
            coverage=[dict(event_id=e['event_id'], candidate_ids=[e['id']],
                           review_note='Source reviewed.', causal_or_passive_scores_used=False)
                      for e in entries])
        path = out / 'causal_pilot/selection_reviews/mathvision_wild.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(request))
        yield path, request, receipt, originals


def test_sharded_pilot_round_trip_preserves_membership_and_strata(packet):
    path, _, _, originals = packet
    reference = module.freeze_pilot(path, object())
    result = module.load_frozen_pilot(reference, object())
    assert len(result['selected_entries']) == 32
    assert {e['native_run_id'] for e in result['selected_entries']} == {'old_prefix', 'shard'}
    assert all(e['causal_pilot_frozen'] is False for e in originals.values())


@pytest.mark.parametrize('defect', ['wrong_owner', 'missing_owner', 'duplicate_owner',
    'wrong_review', 'foreign_provenance', 'missing_fresh_demand', 'scores_used', 'deferred'])
def test_unbound_candidate_or_unapproved_selection_rejected(packet, defect):
    path, request, receipt, _ = packet
    owners = request['bindings']['photo']['runs']
    if defect == 'wrong_owner':
        owners[0]['native_run_id'] = 'foreign'
    elif defect == 'missing_owner':
        owners[0]['event_ids'].pop(0)
    elif defect == 'duplicate_owner':
        owners[1]['event_ids'].append(owners[0]['event_ids'][0])
    elif defect == 'wrong_review':
        owners[0]['review_path'] = 'foreign_reviews'
    elif defect == 'foreign_provenance':
        receipt['unit_provenance'][0]['native_run_id'] = 'foreign'
    elif defect == 'missing_fresh_demand':
        request['eligibility_decisions'][0]['fresh_visual_retrieval_demand'] = False
    elif defect == 'scores_used':
        request['causal_or_passive_scores_used'] = True
    else:
        request['benchmark'] = 'mathsight'
    path.write_text(json.dumps(request))
    with pytest.raises(ValueError):
        module.freeze_pilot(path, object())
    assert not (module.OUT / 'causal_pilot/frozen/mathvision_wild.json').exists()


def test_frozen_pilot_cannot_be_overwritten_or_silently_recompiled(packet):
    path, _, _, originals = packet
    reference = module.freeze_pilot(path, object())
    with pytest.raises(FileExistsError):
        module.freeze_pilot(path, object())
    originals[0]['source_groups']['T'] = [999]
    with pytest.raises(ValueError, match='re-compilation'):
        module.load_frozen_pilot(reference, object())
