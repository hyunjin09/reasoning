"""Verify the discovery stopping branch without inventing held-out estimates."""
from collections import Counter
from pathlib import Path
import subprocess

import pyarrow.parquet as pq
from PIL import Image

from scripts.stage11b.common import ROOT, load, save, sha, now
from scripts.stage11b.analyze_remaining_discovery import reviewed_results
from scripts.stage11b.futility import forward_upper_bound
from scripts.stage11b.protocol import in_stratum


def main():
    selection = load(ROOT / 'stage11b_selection_rule.json')
    resource = load(ROOT / 'stage11b_resource_accounting.json')
    assert selection['status'] == 'NO_GO' and selection['frozen']
    assert resource['final'] and resource['under_hard_limit']
    assert resource['all_stage_allocations_released']
    assert sum(r['allocated_gpu_seconds_observed'] for r in resource['jobs']) == resource['allocated_gpu_seconds_observed']
    live = set(subprocess.check_output(['squeue', '-u', 'hyunjin', '-h', '-o', '%i'], text=True).split())
    assert not live.intersection(str(r['slurm_job_id']) for r in resource['jobs'])

    config = load(ROOT / 'config.json')
    assert sha(ROOT / 'stage11b_equal_evidence_spec.md') == config['spec_sha256']
    tasks = load(ROOT / 'discovery_tasks.json')
    assert sha(ROOT / 'discovery_tasks.json') == config['manifest_sha256']['discovery']
    assert sha(config['discovery_manifest']) == tasks['manifest_sha256']
    for path, expected in config['source_sha256'].items():
        assert sha(path) == expected, path
    execution = load(ROOT / 'source_feasible_execution.json')
    assert sha('scripts/stage11b/resume_source_feasible.py') == execution['worker_sha256']
    assert sha(ROOT / 'source_feasible_tasks.json') == execution['manifest_sha256']
    evidence = load(ROOT / 'annotations/discovery_evidence_final.json')
    source = load(ROOT / 'stage11b_discovery_manifest_v2.json')['rows']
    reserve = load(ROOT / 'audit/heldout_reserve_v2.json')['rows']
    assert len(source) == len(evidence['rows']) == 128
    assert len({r['family_id'] for r in source}) == 128
    assert not {r['family_id'] for r in source}.intersection(r['family_id'] for r in reserve)
    assert sum(r['eligible'] for r in evidence['rows']) == 49
    assert not evidence['model_outcomes_opened']
    pruning = load(ROOT / 'audit/source_pruning_compute_record_v1.json')
    for packet_path in (ROOT / 'packets').glob('partial_answer_review_v*.json'):
        packet = load(packet_path)
        assert evidence['at'] < packet['at'] and pruning['at'] < packet['at']
        version = packet_path.stem.rsplit('_v', 1)[1]
        review = load(ROOT / 'annotations' / f'partial_answers_v{version}.json')
        assert packet['at'] <= review['at']

    results = reviewed_results()
    valid_receipts = []
    for queue in ['discovery', 'source_feasible']:
        for path in (ROOT / queue / 'results').glob('*/result.json'):
            receipt = load(path)
            assert sha(path.parent / 'input.json') == receipt['input_sha256']
            assert sha(path.parent / 'generation.json') == receipt['generation_sha256']
            assert receipt['config_sha256'] == sha(ROOT / 'config.json')
            if not receipt['budget_interrupted']:
                valid_receipts.append(receipt)
    assert len(valid_receipts) == len(results)
    assert {r['task_id'] for r in valid_receipts} == set(results)
    scored = load(ROOT / 'audit/discovery_scored.json')['rows']
    assert len(scored) == len({r['task_id'] for r in scored}) == 256
    assert pq.read_table(ROOT / 'stage11b_discovery_mode_results.parquet').num_rows == 256
    for row in scored:
        if row['status'] != 'COMPLETED_REVIEWED':
            assert row['correct'] is None
    rule = next(r['rule'] for r in selection['source_only_strata'] if r['possible'])
    eligible = [r for r in evidence['rows'] if r['eligible'] and in_stratum(r, rule)]
    pairs = [(results.get('thinking_' + r['item_id'], {}).get('correct'),
              results.get('instruct_cot_' + r['item_id'], {}).get('correct')) for r in eligible]
    bound = forward_upper_bound(pairs)
    assert bound == selection['observed']['maximum_possible_forward']
    assert bound < 12 or (selection['complete_native_pairs'] and not selection['original_gate']['pass'])
    ambiguous = set()
    for path in (ROOT / 'annotations').glob('partial_answers_v*.json'):
        version = path.stem.rsplit('_v', 1)[1]
        keys = {r['packet_id']: r['task_id'] for r in load(ROOT / 'audit' / f'partial_answer_key_v{version}.json')['rows']}
        ambiguous.update(keys[r['packet_id']] for r in load(path)['rows'] if r.get('possible_alternative_answer'))
    generous_pairs = [(None if 'thinking_' + r['item_id'] in ambiguous else t,
                       False if 'instruct_cot_' + r['item_id'] in ambiguous else c)
                      for r, (t, c) in zip(eligible, pairs)]
    generous_bound = forward_upper_bound(generous_pairs)
    assert generous_bound < 12, 'Stopping proof must survive explicitly flagged literal-answer ambiguity'
    if not selection['complete_native_pairs']:
        assert selection['thinking_accuracy'] is selection['cot_accuracy'] is selection['forward_rate'] is None

    for name in ['heldout_e_star_gold', 'native_results', 'oracle_results']:
        table = pq.read_table(ROOT / f'stage11b_{name}.parquet')
        assert table.num_rows == 0
        assert table.schema.metadata[b'status'] == b'NOT_RUN_DISCOVERY_NO_GO'
    inference = load(ROOT / 'stage11b_primary_inference.json')
    assert not inference['claim3_promoted'] and inference['bootstrap_draws_executed'] == 0
    assert all(inference[k] is None for k in ['P1', 'P2', 'P3', 'P4', 'native_gap', 'oracle_gap', 'closure_fraction'])
    summary = (ROOT / 'stage11b_summary.md').read_text()
    assert summary.count('**Recommendation:**') == 1
    assert inference['recommendation'] in summary
    assert 'batch4' in summary and 'not estimated' in summary
    required = ['equal_evidence_spec.md', 'discovery_manifest.json', 'discovery_e_star_eligibility.parquet',
                'discovery_mode_results.parquet', 'selection_rule.json', 'heldout_manifest.json',
                'heldout_e_star_gold.parquet', 'e_star_sufficiency_review.json', 'native_results.parquet',
                'oracle_results.parquet', 'oracle_validity.json', 'primary_inference.json',
                'discordant_analysis.json', 'resource_accounting.json', 'summary.md']
    artifact_hashes = {name: sha(ROOT / ('stage11b_' + name)) for name in required}
    figures = ['figure1_causal_design', 'figure2_discovery_yield_map', 'figure3_native_vs_oracle',
               'figure4_gap_decomposition', 'figure5_secondary_native_evidence']
    for name in figures:
        for suffix in ['png', 'pdf']:
            path = ROOT / 'figures' / f'{name}.{suffix}'
            assert path.stat().st_size > 1000
            artifact_hashes[str(path.relative_to(ROOT))] = sha(path)
        with Image.open(ROOT / 'figures' / f'{name}.png') as img:
            img.verify()
    save(ROOT / 'audit/final_closure_audit.json', dict(at=now(), passed=True,
        required_artifacts=15, optional_artifacts='Explicitly NOT_RUN in conditional_artifact_status.json',
        figure_pairs=5, valid_native_outputs=len(results),
        source_eligibility=dict(Counter(r['eligibility'] for r in evidence['rows'])),
        maximum_possible_forward=bound, missingness_preserved=True,
        generous_bound_with_flagged_answer_ambiguity=generous_bound,
        ambiguous_extraction_tasks=sorted(ambiguous),
        source_evidence_and_pruning_before_answer_packets=True,
        immutable_scientific_sources_match_config=True, all_stage_gpus_released=True,
        artifact_sha256=artifact_hashes, no_oracle_inference_or_next_experiment=True))
    print('PASS: provenance, chronology, missingness, logical gate, conditional artifacts, GPU release and report inventory')


if __name__ == '__main__':
    main()
