from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.stage7a_bench import pilot_freeze_v2 as module
from scripts.stage7a_bench.causal_provenance_v2 import object_sha
from scripts.stage7a_bench.tests.test_pilot_selection_v2 import fixture
from scripts.stage7a.common import sha


@pytest.fixture
def packet(tmp_path, monkeypatch):
    root = tmp_path
    out = root / 'outputs/stage7a_bench_v2'
    monkeypatch.setattr(module, 'ROOT', root)
    monkeypatch.setattr(module, 'OUT', out)
    screen, counts, entries, decisions, selected, families = fixture()
    evidence = out / 'audit/evidence.json'
    evidence.parent.mkdir(parents=True)
    evidence.write_text('{}')
    receipt = dict(screen=screen, frozen_counts=counts, family_map=families,
        generated_event_ids=[e['event_id'] for e in entries]+['no_candidate'],
        artifact_sha256={str(evidence.relative_to(root)):sha(evidence)})
    monkeypatch.setattr(module, 'load_completed_screen', lambda *args:deepcopy(receipt))
    monkeypatch.setattr(module, 'dependency_hashes', lambda:{str(evidence.relative_to(root)):sha(evidence)})
    candidates = []
    original = {}
    for i, (entry, decision) in enumerate(zip(entries, decisions, strict=True)):
        entry.update(native_run_id='native_run', native_index=i,
            annotation_path='annotation'+str(i), source_annotation=dict(claim_index=0))
        original[i] = deepcopy(entry)
        path = out / 'causal_pilot/prepared_candidates' / (entry['id']+'.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(entry))
        candidates.append(dict(path=str(path.relative_to(root)),sha256=sha(path)))
        decision.update(entry_sha256=object_sha(entry), fresh_visual_retrieval_demand=True,
            fresh_demand_review_note='First source read; actual prompt and earlier reasoning reviewed.')
    # Native re-compilation is tested separately against real tokenizer artifacts.
    monkeypatch.setattr(module, 'load_native_claim', lambda run,manifest,index,*args:deepcopy(original[index]))
    monkeypatch.setattr(module, 'load_reviewed_controls', lambda entry:({},dict(status='UNAVAILABLE')))
    request = dict(status='REVIEWED_PILOT_SELECTION_REQUEST',benchmark='charxiv',
        causal_or_passive_scores_used=False, selection_review_note='Full native pool reviewed before scores.',
        bindings={'image_present':dict(native_run_id='native_run',manifest='manifest',review_path='reviews')},
        candidates=candidates, eligibility_decisions=decisions, selected_ids=selected,
        coverage=[dict(event_id=e['event_id'],candidate_ids=[e['id']],
            review_note='Direct singleton claim source review.',causal_or_passive_scores_used=False) for e in entries]+
            [dict(event_id='no_candidate',candidate_ids=[],review_note='No identifiable literal source read.',
                causal_or_passive_scores_used=False)])
    path = out / 'causal_pilot/selection_reviews/charxiv.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(request))
    return path, request, receipt, original, evidence


def save_request(packet):
    path, request, *_ = packet
    path.write_text(json.dumps(request))


def test_freeze_round_trip_revalidates_and_marks_only_selected_entries(packet):
    path, _, _, original, _ = packet
    reference = module.freeze_pilot(path, object())
    frozen = module.load_frozen_pilot(reference, object())
    assert frozen['status'] == 'FROZEN_BEFORE_CAUSAL_SCORING'
    assert len(frozen['selected_entries']) == 32
    assert all(e['causal_pilot_frozen'] is True for e in frozen['selected_entries'])
    assert all(e['causal_pilot_frozen'] is False for e in original.values())


def test_existing_pilot_cannot_be_overwritten_or_refrozen(packet):
    path, *_ = packet
    reference = module.freeze_pilot(path, object())
    before = (module.ROOT/reference['path']).read_bytes()
    with pytest.raises(FileExistsError):
        module.freeze_pilot(path, object())
    assert (module.ROOT/reference['path']).read_bytes() == before


@pytest.mark.parametrize('mutation',['missing_coverage','duplicate_coverage','missing_candidate',
    'foreign_candidate','missing_fresh_demand','scores_used','candidate_changed','wrong_run'])
def test_selection_request_rejects_omission_or_unverified_candidates(packet, mutation):
    path, request, *_ = packet
    if mutation=='missing_coverage':request['coverage'].pop()
    elif mutation=='duplicate_coverage':request['coverage'].append(deepcopy(request['coverage'][0]))
    elif mutation=='missing_candidate':request['coverage'][0]['candidate_ids']=[]
    elif mutation=='foreign_candidate':request['coverage'][0]['candidate_ids'].append('foreign')
    elif mutation=='missing_fresh_demand':request['eligibility_decisions'][0]['fresh_visual_retrieval_demand']=False
    elif mutation=='scores_used':request['causal_or_passive_scores_used']=True
    elif mutation=='candidate_changed':
        target=module.ROOT/request['candidates'][0]['path'];entry=json.loads(target.read_text())
        entry['source_groups']['T']=[999];target.write_text(json.dumps(entry))
        request['candidates'][0]['sha256']=sha(target)
    elif mutation=='wrong_run':request['bindings']['image_present']['native_run_id']='other_run'
    save_request(packet)
    with pytest.raises(ValueError):module.freeze_pilot(path, object())
    assert not (module.OUT/'causal_pilot/frozen/charxiv.json').exists()


@pytest.mark.parametrize('mutation',['request','evidence','freeze','native_entry'])
def test_worker_load_rejects_changes_after_freezing(packet, mutation):
    path, request, receipt, original, evidence = packet
    reference=module.freeze_pilot(path, object())
    if mutation=='request':request['selection_review_note']='changed';save_request(packet)
    elif mutation=='evidence':evidence.write_text('{"changed":true}')
    elif mutation=='freeze':
        target=module.ROOT/reference['path'];saved=json.loads(target.read_text())
        saved['selected_entries'][0]['source_groups']['T']=[999];target.write_text(json.dumps(saved))
    elif mutation=='native_entry':original[0]['source_groups']['T']=[999]
    with pytest.raises(ValueError):module.load_frozen_pilot(reference, object())


def test_dependency_receipt_includes_all_unchanged_inherited_definitions():
    inherited=json.loads((module.OUT/'config/inherited_causal_definition_freeze.json').read_text())
    receipt=module.dependency_hashes()
    assert all(receipt.get(path)==digest for path,digest in inherited['dependency_sha256'].items())


def test_changed_inherited_definition_prevents_freeze(monkeypatch):
    original=module.sha
    target=module.ROOT/'code/visual_reasoning/stage7a/classification.py'
    monkeypatch.setattr(module,'sha',lambda path:'changed' if Path(path)==target else original(path))
    with pytest.raises(ValueError,match='Inherited'):
        module.dependency_hashes()
