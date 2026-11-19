"""Continuation must revalidate semantic evidence, not trust a decision string."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from scripts.stage7a.common import write_json, write_jsonl, sha
from scripts.stage7a_bench.causal_provenance_v2 import object_sha
from scripts.stage7a_bench.mathwild_semantic_ledger_v5 import build_ledger
from scripts.stage7a_bench.mathwild_feasibility_v5 import evaluate_gate
from scripts.stage7a_bench.tests.test_mathwild_feasibility_v5 import packet, local_failure
from scripts.stage7a_bench import mathwild_gate_checkpoint_v6 as verifier


@pytest.fixture
def checkpoint(monkeypatch):
    actual = Path(__file__).resolve().parents[3]
    with TemporaryDirectory(dir=actual / 'outputs/stage7a_bench_v2/audit') as tmp:
        root = Path(tmp)
        out = root / 'outputs/stage7a_bench_v2'
        monkeypatch.setattr(verifier, 'ROOT', root)
        monkeypatch.setattr(verifier, 'OUT', out)
        coverage, initial, pairs, pair_ids = packet()
        coverage.update(status='COMPLETE_INTERIM_COVERAGE', unit_provenance=[],
                        run_status={'shard': 'COMPLETED'})
        for row in initial[:12]:
            local_failure(row)
        assessments = []
        for review, row in zip(coverage['reviews'], initial):
            claim = review['claims'][0]
            claim.update(source_id='source', readout='wrong', ground_truth='correct')
            assessments.append(dict(row, native_index=review['native_index'],
                base_id=review['base_id'], source_id='source', emitted_readout='wrong',
                source_truth='correct', demand='singleton', claim_sha256=object_sha(claim),
                semantic_review_object_sha256=object_sha(review)))
        monkeypatch.setattr(verifier, 'load_gate_coverage', lambda require_complete: deepcopy(coverage))

        def save(name, value, lines=False):
            path = out / name
            (write_jsonl if lines else write_json)(path, value)
            return dict(path=str(path.relative_to(root)), sha256=sha(path))

        source = save('native_screen/gate96_source_reviews/source.json', {'entries': assessments})
        paired = save('cohort/benchmark_manifests/screenshot.jsonl',
                      [dict(base_id=b) for b in pair_ids], True)
        save('cohort/sample_freeze.json', {'native_screen': {'mathvision_wild_screenshot':
             dict(manifest=paired['path'], sha256=paired['sha256'], count=64)}})
        photo = save('cohort/benchmark_manifests/photo.jsonl',
                     [dict(image_path=str(out / 'source.png'))], True)
        save('config/mathwild_gate96_selection_v5.json', {'manifest': photo})
        ledger, bindings = build_ledger(coverage, assessments)
        value = dict(status='FROZEN_MATHWILD96_SEMANTIC_FEASIBILITY',
            coverage=save('audit/coverage.json', coverage), source_bindings=[source],
            verified_source_evidence_sha256={source['path']: source['sha256']},
            claim_bindings=bindings, ledger=ledger, paired_assessments=pairs,
            paired_manifest=paired,
            result=evaluate_gate(coverage, ledger, pairs, pair_ids))
        reference = save('audit/gate.json', value)
        yield root, out, coverage, value, reference, save


def test_complete_semantic_gate_recomputes_the_decision(checkpoint):
    assert verifier.verify_mathwild_gate(checkpoint[4])['decision'] == 'CONTINUE_FROZEN_MATHWILD_SAMPLE'


@pytest.mark.parametrize('defect', ['provisional', 'changed_result', 'changed_ledger',
    'changed_source', 'missing_review', 'stale_snapshot', 'missing_pair', 'outside_path',
    'invented_pair_transition', 'different_paired_manifest'])
def test_unverified_gate_cannot_release_the_remaining_sample(checkpoint, defect):
    root, out, coverage, value, reference, save = checkpoint
    if defect == 'provisional':
        value['status'] = 'PROVISIONAL_SEMANTIC_ELIGIBILITY_NOT_A_GATE_DECISION'
    elif defect == 'changed_result':
        value['result']['decision'] = 'STOP_MATHWILD_LOW_YIELD'
    elif defect == 'changed_ledger':
        value['ledger'][0]['source_localizable_failure_candidate'] = False
    elif defect == 'changed_source':
        (root / value['source_bindings'][0]['path']).write_text('{}')
    elif defect == 'missing_review':
        coverage['reviews'].pop()
    elif defect == 'stale_snapshot':
        coverage['reviews'][0]['claims'][0]['ground_truth'] = 'different'
    elif defect == 'missing_pair':
        value['paired_assessments'].pop()
    elif defect == 'invented_pair_transition':
        value['paired_assessments'][0].update(interpretable_transition=True, evidence_verified=True)
    elif defect == 'different_paired_manifest':
        value['paired_manifest'] = save('cohort/benchmark_manifests/other.jsonl',
            [dict(base_id=f'b{i}') for i in range(64)], True)
    else:
        value['verified_source_evidence_sha256']['/not-an-approved-source'] = 'bad'
    reference = save('audit/gate.json', value)
    with pytest.raises(ValueError):
        verifier.verify_mathwild_gate(reference)
