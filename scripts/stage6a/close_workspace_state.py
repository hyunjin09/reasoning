"""Close the approved Stage6A documentation after verified release artifacts.

This is deterministic reporting, not selection or execution of another research
action. Unexpected results or intervening documentation edits stop the closeout.
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.stage6a.inventory import OUT, ROOT


PHASE = 'workspace/phase_memory/phase_6a_dedicated_alignment_mirage_retrieval_dynamics_cohort.md'
DOCUMENTS = [PHASE, 'workspace/workflow_state.md', 'workspace/research_plan.md',
             'workspace/env_state.md', 'workspace/decision_log.md',
             'plan/stage6a_execution_checklist.md']
PLAN = 'plan/stage6a_dedicated_alignment_mirage_retrieval_dynamics_cohort_plan.md'
RECOMMENDATION = 'GO — Natural Failure Extension'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def required_artifacts(plan):
    section = plan.split('# 54. Output Structure\n', 1)[1].split('# 55.', 1)[0]
    directory = None
    result = []
    for line in section.splitlines():
        if re.fullmatch(r'  [a-z0-9_]+/', line):
            directory = line.strip().rstrip('/')
        elif re.fullmatch(r'    [a-z0-9_.]+', line):
            assert directory is not None
            result.append(directory + '/' + line.strip())
    assert len(result) >= 60 and len(result) == len(set(result))
    return result


def replace_between(text, start, end, body):
    assert text.count(start) == 1 and text.count(end) == 1
    left, rest = text.split(start, 1)
    _, right = rest.split(end, 1)
    return left + start + body.rstrip() + '\n\n' + end + right


def section(text, heading, body):
    start = '## ' + heading + '\n\n'
    assert text.count(start) == 1
    left, rest = text.split(start, 1)
    _, separator, right = rest.partition('\n## ')
    return left + start + body.rstrip() + '\n' + ('\n## ' + right if separator else '')


def validate_closeout(release, integrity, acceptance, resource, annotation, tables):
    assert integrity['status'] == 'PASS'
    assert release['events'] == integrity['events'] == 2983
    assert release['bases'] == integrity['bases'] == 1276
    assert release['per_cohort_events'] == dict(C1=1199, C2=124, C3=660, C4=1000)
    assert release['per_cohort_bases'] == dict(C1=109, C2=31, C3=136, C4=1000)
    assert release['release_events_sha256'] == integrity['release_sha256'] == acceptance['release_sha256']
    assert acceptance['status'] == 'CONTROLLED_PASS_NATURAL_ATLAS_INSUFFICIENT'
    assert acceptance['gates'] == dict(C1=True, C2=True, C3=True, C4_unbiased_acquisition=True, C4_atlas=False)
    assert acceptance['recommendation'] == RECOMMENDATION
    assert acceptance['C4'] == dict(unbiased_images=1000, matched_pairs=10)
    assert acceptance['next_stage_executed'] is False
    assert acceptance['internal_state_features_used_for_selection'] is False
    assert resource['status'] == 'COMPLETE_MEASURED_NATIVE_RESOURCE_SUMMARY', 'Resource snapshot is not final'
    assert resource['native_terminal_records'] == 3182
    assert resource['physical_repeat_generations'] == 13
    assert resource['native_terminal_records'] == sum(resource['native_completeness'].values())
    assert resource['physical_gpus'] == 4 and resource['new_allocations_requested_by_agent'] == 0
    assert resource['parameter_dtype'] == 'torch.bfloat16'
    assert annotation['status'] == 'PASS' and annotation['events'] == 1992
    assert annotation['complete_manual_prefix_bases'] == 109 and annotation['manual_prefix_spans'] == 1766
    assert annotation['baseline_claims_preserved_in_prefix'] == 105
    assert [t['number'] for t in tables] == list(range(1, 19)), 'Missing, duplicated or reordered summary table'
    assert all(len(row) == len(t['columns']) for t in tables for row in t['rows'])


def render_documents(original, release, resource, annotation, date):
    result = dict(original)
    prefix = 'outputs/stage6a/'
    summary = prefix + 'summaries/stage6a_cohort_summary.md'
    counts = ('The release contains 2,983 events from 1,276 bases: C1 109 bases/1,199 events; '
              'C2 31 families/124 events; C3 136 families/660 events; C4 1,000 images/events.')
    yield_text = ('C1/C2/C3 construction gates pass. C4 has 10 confirmed, 50 unresolved and '
                  '940 no-detected whole-trace object-error labels in the fixed 1,000-image sample. '
                  'The frozen atlas has 10 matched pairs, below the 60-pair minimum. '
                  'The 1–6% protocol identification range is not a confidence interval.')
    annotation_text = (f"All 109 C1 numeric-source prefixes are reviewed: 1,766 spans and 235 secondary ROIs. "
                       f"The controlled annotation audit passes {annotation['events']:,} events/"
                       f"{annotation['reasoning_spans']:,} reasoning spans, preserving all 105 baseline claims "
                       'inside prefixes. Remaining geometry retains explicit unknowns. All C3 responses '
                       'and the C4 labels/matched controls have the recorded manual reviews.')
    compute = (f"Physical acquisition saved {resource['native_terminal_records']:,} terminal records "
               f"({resource['native_completeness'].get('INCOMPLETE', 0)} incomplete) and 13 replay generations, "
               f"totaling {resource['measured_native_device_hours']:.4f} measured device-hours. "
               f"The primary release has {release['native_eos_complete']:,} natural-EOS traces; "
               'terminal capped variants remain in its condition accounting. Device-hours are not elapsed wall time.')
    stop = (f'Sole recommendation: **{RECOMMENDATION}**. This recommends a separately approved plan; '
            'no further acquisition, Stage6B, attention/PCA/causal trajectory analysis or rescue was executed.')
    evidence = f'Summary and all 18 tables: `{summary}`. Release, annotation, ROI, manipulation, split, selection and resource audits are complete.'

    phase = section(result[PHASE], 'Current Objective',
        f'The approved Stage6A cohort construction and audited release are complete on {date}. '
        f'Stop at the sole {RECOMMENDATION} recommendation; another research action is not authorized.')
    phase = section(phase, 'Active Constraints',
        'Stage6A used only the existing four RTX A6000 GPUs in Slurm109385/node03/tmux9. '
        'No new allocation or dataset download was requested. Native generation used the frozen '
        'BF16 Qwen3-VL-4B-Thinking settings, seed1234, temperature .6, top-p .95, top-k20 and '
        '40,960-token natural-EOS cap. Capped responses were retained without reruns.\n\n'
        'Cohort membership, source/template splits, annotation truth/unknowns and the 10-pair C4 atlas '
        'remain frozen. Semantic source utterances/refreshes do not establish causal evidence use. '
        'A recommendation is not authorization for another research action.')
    phase = section(phase, 'Current State',
        f'{counts}\n\n{annotation_text}\n\n{yield_text}\n\n{compute}\n\n{evidence}\n\n'
        'Five C1 intact cap incompletes and the four events of invalid C2 family docvqa56412 '
        'remain raw and outside the primary release. Availability gates and native-EOS feasibility '
        'are reported separately. There are no pending Stage6A acquisition or annotation tasks.\n\n'
        'The full pre-closeout state, including chronology, annotation repairs, test evidence '
        'and acquisition checkpoints, is preserved in '
        '`outputs/stage6a/audit/workspace_state_before_closeout/phase_6a_dedicated_alignment_mirage_retrieval_dynamics_cohort.md`.')
    phase = phase.replace('| partial snapshot |', '| complete; final totals |')
    phase = section(phase, 'Open Candidates',
        f'{stop}\n\nThere is no authorized open execution task. Preserve the negative natural-case yield '
        'and the annotation limits when reviewing a future plan.')
    phase = section(phase, 'Next-Step Decision',
        '- Completed action: the explicitly approved Stage6A cohort construction, acquisition, '
        'annotation, freeze and audited release.\n'
        '- Decision evidence: controlled gates pass, but the fixed natural sample yields only 10 '
        'matched case/control pairs; its 60-pair minimum is unmet.\n'
        f'- Recommendation: {RECOMMENDATION}; no execution is authorized by this recommendation.\n'
        '- Stop condition reached: every fixed terminal record, required output, 18 tables and '
        'the final acceptance report are saved. No further research action was selected.\n\n'
        '### Step Result\n\nThe release is complete with controlled gates passing and the natural '
        f'atlas size gate unmet. The summary is `{summary}`. No next stage was executed.\n\n'
        'The deterministic closeout audit is `outputs/stage6a/audit/workspace_state_closeout.json`. '
        'Human-readable templates and the prescribed branch were reviewed before completion; '
        'the final exact counts, files, tables and hashes were then checked programmatically.')
    result[PHASE] = phase

    path = 'workspace/workflow_state.md'
    text = replace_between(result[path], '# Workflow State\n\n', 'Stage5A is complete and stopped under',
        f'Stage6A is complete and stopped on {date}. Controlled gates pass; the frozen natural '
        f'failure atlas has 10 pairs, below its 60-pair minimum. Sole recommendation: **{RECOMMENDATION}**, '
        f'without next-stage execution. Summary and 18 tables: `{summary}`.\n\n'
        'Earlier state and stop statements below describe completed stages.')
    text = section(text, 'Dashboard',
        f'- Last updated: {date}.\n- Project status: Stage6A complete and stopped.\n'
        f'- Active phase: none; the sole next-stage recommendation is {RECOMMENDATION}.\n'
        '- Final artifacts: all 18 tables and release/semantic/ROI/split/resource audits complete.\n'
        '- Strategic direction: analysis first; further research requires a separately approved action.')
    text = replace_between(text, '## Current Bottleneck\n\n', 'Historical Stage5A bottleneck:',
        'No Stage6A task remains. Controlled construction is usable, but the natural failure atlas '
        'contains only 10 pairs. Review the sole recommendation and its scope before any new acquisition.')
    result[path] = text.replace('## Evidence in Hand\n\n', '## Evidence in Hand\n\n- `' + summary + '`: final cohort, all 18 tables, controlled PASS and insufficient natural atlas yield.\n- `outputs/stage6a/audit/workspace_state_closeout.json`: final artifact/count/hash and documentation closeout checks.\n\n', 1)

    path = 'workspace/research_plan.md'
    text = replace_between(result[path], '# Research Plan\n\n', 'Stage5A is complete and stopped under',
        f'The approved Stage6A plan is complete and stopped on {date}. Its sole '
        f'**{RECOMMENDATION}** recommendation requires a separately approved plan. '
        f'No further acquisition or analysis is authorized. Final evidence: `{summary}`.\n\n'
        'Earlier authorizations and stop statements below are historical.')
    text = re.sub(r'^- Active program stage:.*$', '- Active program stage: none; Stage6A is complete and stopped.', text, count=1, flags=re.M)
    result[path] = re.sub(r'^- Current authorization:.*$', '- Current authorization: Stage6A is fulfilled. Its recommendation does not authorize further acquisition or another analysis stage.', text, count=1, flags=re.M)

    path = 'workspace/env_state.md'
    result[path] = replace_between(result[path], '# Environment State\n\n', 'Historical Stage5A execution:',
        f'Current execution status: Stage6A complete and stopped on {date}.\n\n{compute}\n\n'
        'All Stage6A model work used the existing user allocation Slurm109385/node03/tmux9, '
        'four RTX A6000s, BF16 and the project-local .venv. No package changes, new allocation '
        'request or dataset download. User allocation:240G/48CPUs; GPU experiment bookkeeping:120G/32CPUs. '
        'Final CPU integration and reporting ran as overlapping steps in that allocation. This is '
        'completed-run provenance, not a claim that the allocation remains available afterward.\n\n'
        'Prior allocation108548/node07 was reclaimed at2026-09-07 03:00:24. On2026-09-08 '
        '03:04KST, all four current GPUs were active; the saved observation is '
        '`outputs/stage6a/audit/gpu_retention_20260908_0304kst.json`. '
        'Final resource evidence: `outputs/stage6a/audit/resource_summary.json`.\n\n'
        'Earlier allocation entries below are historical provenance.')

    path = 'plan/stage6a_execution_checklist.md'
    left, _, _ = result[path].partition('Current progress:')
    assert left != result[path]
    result[path] = (left + f'Current progress: steps1–9 complete on {date}. All 70 plan-required '
        f'output files and 18 tables are present and audited. Controlled gates pass; the natural '
        f'atlas has 10 pairs against its 60-pair minimum. Sole recommendation: {RECOMMENDATION}; '
        f'no next stage executed. Final report: `{summary}`.\n')

    path = 'workspace/decision_log.md'
    assert '## D-056' not in result[path], 'Decision log changed; review numbering'
    result[path] += (f'\n## D-056 — Preserve controlled cohort acceptance and insufficient natural-case yield\n\n'
        f'- Date: {date}. Stage6A is complete.\n- Observation: {yield_text}\n'
        '- Supported lesson: construction availability, natural-EOS feasibility, category-protocol '
        'yield and causal grounding are distinct. Keep capped traces, unresolved labels and the '
        'fixed sample; do not enlarge the current sample or change definitions to meet the atlas gate.\n'
        f'- Decision: {RECOMMENDATION}, recommendation only; no next-stage execution.\n'
        f'- Evidence: `{summary}`, `outputs/stage6a/summaries/stage6a_acceptance.json`, '
        '`outputs/stage6a/c4_natural_failure/unbiased_prevalence.json`, '
        '`outputs/stage6a/audit/release_integrity.json`.\n')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare', action='store_true', help='Freeze documentation preimages; does not close the stage')
    args = parser.parse_args()
    config_path = OUT / 'config/workspace_closeout_inputs.json'
    inputs = {name: sha((ROOT / name).read_bytes()) for name in [*DOCUMENTS, PLAN]}
    if args.prepare:
        assert not (OUT / 'cohort/primary_release_manifest.json').exists()
        config_path.write_text(json.dumps(dict(status='PREPARED_NOT_COMPLETE', sha256=inputs), indent=2) + '\n')
        print('Documentation closeout prepared; no completion claim written.')
        return
    assert not (OUT / 'audit/workspace_state_closeout.json').exists(), 'Preserve completed closeout'
    assert inputs == json.loads(config_path.read_text())['sha256'], 'Documentation or plan changed; review before closeout'
    def read(name):
        return json.loads((OUT / name).read_text())
    release = read('cohort/primary_release_manifest.json')
    integrity = read('audit/release_integrity.json')
    acceptance = read('summaries/stage6a_acceptance.json')
    resource = read('audit/resource_summary.json')
    annotation = read('audit/controlled_annotation_integrity.json')
    tables = read('summaries/stage6a_summary_tables.json')
    validate_closeout(release, integrity, acceptance, resource, annotation, tables)
    prevalence = read('c4_natural_failure/unbiased_prevalence.json')
    assert prevalence['whole_trace_label_counts'] == dict(no_detected_object_hallucination=940, hallucination=10, UNRESOLVED=50)
    assert prevalence['confirmed_positive_fraction'] == .01
    assert prevalence['annotation_protocol_uncertainty_interval'] == [.01, .06]
    assert prevalence['pending_claim_reviews'] == 0
    from scripts.stage6a.source_annotations import secondary_sources
    assert sum(len(rows) for rows in secondary_sources().values()) == 235
    assert sha((OUT / 'cohort/primary_release_events.jsonl').read_bytes()) == release['release_events_sha256']
    required = required_artifacts((ROOT / PLAN).read_text())
    assert len(required) == 70 and all((OUT / name).is_file() for name in required), 'Missing plan-required artifact'
    for name in required:
        if name.endswith('.json'):
            read(name)
    summary = (OUT / 'summaries/stage6a_cohort_summary.md').read_text()
    assert all(f"## {t['number']}. {t['title']}\n" in summary for t in tables)
    assert (OUT / 'summaries/next_analysis_recommendation.md').read_text().startswith('# ' + RECOMMENDATION + '\n')
    original = {name: (ROOT / name).read_text() for name in DOCUMENTS}
    date = datetime.now(ZoneInfo('Asia/Seoul')).date().isoformat()
    rendered = render_documents(original, release, resource, annotation, date)
    # Prepare every replacement and preserve every preimage before any mutation.
    backup = OUT / 'audit/workspace_state_before_closeout'
    backup.mkdir(exist_ok=False)
    for name, text in original.items():
        (backup / Path(name).name).write_text(text)
    written = {}
    for name, text in rendered.items():
        target = ROOT / name
        assert sha(target.read_bytes()) == inputs[name], 'Intervening document edit'
        temporary = target.with_suffix('.stage6a_closeout.tmp')
        temporary.write_text(text)
        temporary.replace(target)
        written[name] = sha(target.read_bytes())
    audit = dict(status='PASS', completed_at=datetime.now(timezone.utc).isoformat(),
        required_artifacts=len(required), tables=18, release_sha256=release['release_events_sha256'],
        document_preimages=inputs, document_outputs=written, recommendation=RECOMMENDATION,
        review_scope='Pre-reviewed templates and frozen branch; final exact counts, required files, table structure and hashes checked programmatically.',
        no_follow_on_research_executed=True)
    (OUT / 'audit/workspace_state_closeout.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
