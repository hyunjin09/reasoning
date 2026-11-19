"""Verify the frozen repair universe without reading causal values or using CUDA."""
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from scripts.stage6b.common import ROOT, SOURCE, read_json, sha, verify_stage6a, write_json, write_jsonl

OUT = ROOT / 'outputs/stage6br'


def rows(path):
    with Path(path).open() as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def main():
    policy = (ROOT / 'ACCESS_POLICY.md').read_text()
    section = policy.split('## Allowed Read/Search Roots', 1)[1].split('## Allowed Write Roots', 1)[0]
    allowed = [ROOT if p == '.' else Path(p) for p in re.findall(r'^- `([^`]+)`', section, re.M)]

    def checked(path):
        p = Path(path).resolve()
        if not any(p.is_relative_to(r) for r in allowed):
            raise ValueError('Path outside allowed read roots: ' + str(p))
        if not p.exists():
            raise FileNotFoundError(p)
        return p

    prior = verify_stage6a()
    # Lookup starts with the project link; inherited resolved dataset roots are
    # checked next. No downloads or external cache creation are needed.
    link = ROOT / 'datasets'
    link_status = str(checked(link)) if link.is_symlink() or link.exists() else 'absent'
    inventory = []
    for row in prior['datasets_lookup']['allowed_data_roots_verified']:
        if row['dataset'] in {'MathVerse', 'MathVision', 'MathVista'}:
            inventory.append({'dataset': row['dataset'], 'roots': [str(checked(x['path'])) for x in row['roots']]})
    model = checked(prior['model_checkpoint'])
    checked(model / 'config.json')
    release = {r['event_id']: r for r in rows(SOURCE / 'cohort/primary_release_events.jsonl') if r['cohort'] == 'C1'}
    bases = {r['base_id']: r for r in release.values()}
    assert len(release) == 1199 and len(bases) == 109
    assert Counter(r['dataset'] for r in bases.values()) == {'MathVerse': 34, 'MathVision': 31, 'MathVista': 44}
    for r in release.values():
        assert r['split'] == bases[r['base_id']]['split']
    images = {str(checked(r['image_path'])) for r in release.values() if r.get('image_path')}
    native = {}
    artifacts = set()
    for r in rows(SOURCE / 'traces/controlled_native_index.jsonl'):
        if r['event_id'] not in release:
            continue
        native[r['event_id']] = {k: r[k] for k in ['event_id', 'base_id', 'input_metadata_artifact', 'generation_artifact', 'tokens_artifact']}
        artifacts.update(str(checked(r[k])) for k in ['input_metadata_artifact', 'generation_artifact', 'tokens_artifact'])
    assert set(native) == set(release)
    candidates = [r for r in rows(SOURCE / 'traces/controlled_future_causal_anchors.jsonl') if r['event_id'] in release]
    counts = Counter(t for r in candidates for t in r['anchor_types'])
    assert {k: counts[k] for k in ['demand_transition', 'matched_no_transition_candidate', 'refresh', 'wrong_claim']} == {
        'demand_transition': 1385, 'matched_no_transition_candidate': 3683, 'refresh': 377, 'wrong_claim': 97}
    by_condition = defaultdict(Counter)
    for r in candidates:
        by_condition[release[r['event_id']]['condition']].update(r['anchor_types'])
    protected = {str(SOURCE / p): v for p, v in prior['protected_stage6a_sha256'].items()}
    for path in [SOURCE / 'traces/controlled_demand_annotations.jsonl', SOURCE / 'traces/controlled_transition_annotations.jsonl',
                 SOURCE / 'traces/controlled_native_index.jsonl', ROOT / 'outputs/stage6b/trajectory/pca_discovery.json',
                 ROOT / 'outputs/stage6b/trajectory/normalization.json', ROOT / 'outputs/stage6b/trajectory/trajectory_metrics.jsonl',
                 ROOT / 'plan/stage6br_dynamic_demand_readout_panel_repair_plan.md']:
        protected[str(path)] = sha(checked(path))
    write_json(OUT / 'audit/protected_inputs.json', protected, freeze=True)
    # Operational index is never passed wholesale into an annotation packet.
    index = []
    for eid, r in release.items():
        index.append({k: r[k] for k in ['event_id', 'base_id', 'dataset', 'condition', 'split', 'group_id', 'question', 'prompt', 'image_path']} | native[eid])
    write_jsonl(OUT / 'inputs/c1_index.jsonl', index, freeze=True)
    state = subprocess.check_output(['squeue', '-h', '-j', '111485', '-o', '%T %N %C %b'], text=True).strip()
    result = {'status': 'CPU_INPUT_PREFLIGHT_PASS', 'checked_at': datetime.now().astimezone().isoformat(),
              'bases': len(bases), 'native_traces': len(native), 'dataset_bases': Counter(r['dataset'] for r in bases.values()),
              'split_bases': Counter(r['split'] for r in bases.values()), 'candidate_counts': counts,
              'candidate_counts_by_condition': by_condition, 'verified_images': len(images), 'verified_native_artifacts': len(artifacts),
              'dataset_lookup': {'project_link': link_status, 'existing_roots': inventory, 'downloaded': False},
              'model_checkpoint': str(model), 'protected_inputs': 'audit/protected_inputs.json',
              'gpu_allocation': {'job_id': '111485', 'tmux': '10', 'observed_state': state, 'launch_ready': state.startswith('RUNNING node06 ')},
              'gpu_computation_performed': False, 'panel_gate_assessed': False,
              'count_reconciliation': 'Plan counts cover all11conditions; intact alone has477transitions/535hold candidates/375refreshes/96wrong anchors.',
              'git_metadata_present': (ROOT / '.git').exists()}
    write_json(OUT / 'audit/input_preflight.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
