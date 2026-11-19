"""Revalidate the frozen96-review semantic gate before any later native release.

Measured clean/photo transitions require their own native provenance adapter;
this checkpoint supports the current unrun, explicitly unknown clean condition.
"""
from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha
from scripts.stage7a_bench.mathwild_gate_coverage_v5 import load_gate_coverage
from scripts.stage7a_bench.mathwild_semantic_ledger_v5 import build_ledger
from scripts.stage7a_bench.mathwild_feasibility_v5 import evaluate_gate

OUT = ROOT / 'outputs/stage7a_bench_v2'


def verify_mathwild_gate(reference):
    def verified(ref, external_sources=()):
        path = (ROOT / ref['path']).resolve()
        if not path.is_relative_to(OUT) and path not in external_sources:
            raise ValueError('Gate evidence outside the stage or exact frozen image sources')
        if sha(path) != ref['sha256']:
            raise ValueError('Frozen gate evidence changed')
        return path

    packet = read_json(verified(reference))
    if packet.get('status') != 'FROZEN_MATHWILD96_SEMANTIC_FEASIBILITY':
        raise ValueError('A frozen complete96-review checkpoint is required')
    coverage = load_gate_coverage(require_complete=True)
    saved = read_json(verified(packet['coverage']))
    if saved.get('status') != 'COMPLETE_INTERIM_COVERAGE' or any(
            saved.get(key) != coverage.get(key) for key in
            ('reviews', 'screen', 'family_map', 'unit_provenance', 'run_status')):
        raise ValueError('Frozen96-review snapshot differs from verified native coverage')
    selection = read_json(OUT / 'config/mathwild_gate96_selection_v5.json')
    photos = read_jsonl(verified(selection['manifest']))
    external_sources = {(ROOT / row['image_path']).resolve() for row in photos}
    for name, digest in packet['verified_source_evidence_sha256'].items():
        verified(dict(path=name, sha256=digest), external_sources)
    assessments = []
    for ref in packet['source_bindings']:
        assessments.extend(read_json(verified(ref))['entries'])
    ledger, bindings = build_ledger(coverage, assessments)
    if ledger != packet['ledger'] or bindings != packet['claim_bindings']:
        raise ValueError('Gate ledger differs from exact bound manual source judgments')
    pairs = packet['paired_assessments']
    if any(pair['interpretable_transition'] is not None for pair in pairs):
        raise ValueError('Measured pair transitions require separately verified native pair bindings')
    paired_path = verified(packet['paired_manifest'])
    frozen_pair = read_json(OUT / 'cohort/sample_freeze.json')['native_screen']['mathvision_wild_screenshot']
    if ((ROOT / frozen_pair['manifest']).resolve() != paired_path or
            frozen_pair['sha256'] != sha(paired_path) or frozen_pair['count'] != 64):
        raise ValueError('Pairing differs from the original frozen64-item screenshot cohort')
    paired_rows = read_jsonl(paired_path)
    if len(paired_rows) != 64:
        raise ValueError('All original64 paired items must retain explicit missingness')
    result = evaluate_gate(coverage, ledger, pairs, [r['base_id'] for r in paired_rows])
    if result != packet['result']:
        raise ValueError('Frozen gate result does not reproduce from semantic evidence')
    if result['decision'] not in ('CONTINUE_FROZEN_MATHWILD_SAMPLE', 'STOP_MATHWILD_LOW_YIELD'):
        raise ValueError('Unresolved semantic feasibility cannot release the next benchmark')
    return result
