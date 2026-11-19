"""Archive closure code and verify the completed, immutable research package."""
from pathlib import Path
import shutil
from scripts.stage14e.common import P, load, save, sha, now


def main():
    verification = load(P / 'audit/final_execution_verification_v1.json')
    resources = load(P / 'audit/resource_accounting_final_v1.json')
    assert verification['all_cycle_allocations_terminal']
    assert resources['new_actual_gpu_hours'] <= 24
    assert load(P / 'audit/execution_checklist_final_v1.json')['follow_on_launched'] is False
    cases = load(P / 'analysis/final_casebook_v1.json')['records']
    expected = set(load(P / 'manifests/final_execution_registry_v1.json')['families'])
    assert len(cases) == 32 and {r['item_id'] for r in cases} == expected
    for name in ['sava_failure_postmortem_v1.md', 'prior_art_and_hypotheses_v1.md',
                 'diagnostic_v1.md', 'development_revision_v2.md',
                 'final_acquisition_review_v1.md', 'final_research_report_v1.md',
                 'final32_casebook_v1.md', 'final_answer_change_casebook_v1.md']:
        assert (P / 'reports' / name).stat().st_size > 0
    destination = P / 'audit/code_at_closure_v1'
    destination.mkdir(exist_ok=False)
    copied = {}
    for source in sorted(Path('scripts/stage14e').iterdir()):
        if source.is_file() and source.suffix in ['.py', '.sh', '.md']:
            target = destination / source.name
            shutil.copyfile(source, target)
            assert sha(source) == sha(target)
            copied[str(target)] = sha(target)
    save(P / 'audit/closure_analysis_code_review_v2.json', dict(at=now(),
        reviewer='Main agent; no independent review claimed', code_snapshot=copied,
        actual_integration='32families/96logical/77physical/19aliases; all receipts, hashes, '
            'inputs, review joins, inherited scoring, source-stratified bootstrap and resource audit completed.',
        findings=[
            'Final acquisition labels precede gold-blind response review and aggregate correctness scoring.',
            'No final-score-driven annotation, method revision, family exclusion or new inference.',
            'Aliases remain native outcomes; zero useful evidence does not imply every statement false.',
            'Matched final hardware; prior development hardware and enriched diagnostic-target limitations disclosed.',
            'Report tables formatted correctly; raw parser/manual/gold fields remain separate.',
            'All finite GPU allocations terminal; failed/startup/cancelled allocations charged.'],
        historical_preservation_sha256=sha(P / 'audit/historical_preservation_final_v1.json')))
    seal_path = P / 'audit/final_closure_seal_v1.json'
    excluded, files = {}, {}
    for path in sorted(P.rglob('*')):
        if not path.is_file() or path == seal_path:
            continue
        if path.name in ['resource_ledger.json', 'progress.json']:
            excluded[str(path)] = 'Mutable operational status; terminal accounting/verification archived separately.'
        else:
            files[str(path)] = sha(path)
    save(seal_path, dict(at=now(), status='COMPLETE_STOP', files=files,
        excluded=excluded, additional_gpu_hours=resources['new_actual_gpu_hours'],
        historical_sava_gpu_hours=resources['historical_sava_gpu_hours'],
        no_follow_on_launched=True))
    assert all(sha(path) == digest for path, digest in files.items())
    print('Verified closure seal:', len(files), 'files;', resources['new_actual_gpu_hours'], 'new GPUh')


if __name__ == '__main__':
    main()
