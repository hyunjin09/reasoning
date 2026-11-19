"""Seal technical validity/pathology only. No accuracy or bottleneck computation."""
import argparse
import json
from pathlib import Path
import pandas as pd
from scripts.stage12br.common import ROOT, load, save, sha, now
from scripts.stage12br.protocol import validity, gate
from scripts.stage12br.review import checked_generation
from scripts.stage12br.resources import account

ENDING = dict(VALIDITY_REPAIRED='VALIDITY_REPAIRED — Stage12B scientific profiling may resume',
              SCOREABILITY_FAIL='SCOREABILITY_FAIL — do not resume Stage12B',
              INPUT_INTEGRITY_FAIL='INPUT_INTEGRITY_FAIL — do not resume Stage12B')


def main(decisions_path):
    m=load(ROOT/'stage12br_validation_manifest.json')
    d=load(decisions_path)
    assert d['correctness_opened'] is False
    annotations={r['task_id']:r for r in d['rows']}
    assert len(d['rows'])==len(annotations)==36 and set(annotations)=={t['task_id'] for t in m['tasks']}
    for p,h in load(ROOT/'audit/prospective_freeze.json')['files'].items():assert sha(p)==h,p
    for p,h in load(ROOT/'config.json')['source_sha256'].items():assert sha(p)==h,p
    old_hashes=load(ROOT/'audit/preserved_stage12b_hashes.json')['files']
    for p,h in old_hashes.items():assert sha(p)==h,p
    result_rows=[];label_rows=[]
    for task in m['tasks']:
        g,checks=checked_generation(task);r=annotations[task['task_id']]
        generation_path=ROOT/'generations'/task['task_id']/'generation.json'
        assert r['generation_sha256']==sha(generation_path)
        assert isinstance(r['scoreable'],bool) and r['reason'] and r['quotes']
        assert all(q and q in g['raw_decoded_response'] for q in r['quotes'])
        assert not r['scoreable'] or r['extracted_outcome']
        r5=False
        if task['arm'] in 'NO':
            assert set(r['labels'])=={f'R{i}' for i in range(1,6)}
            assert all(isinstance(v,bool) for v in r['labels'].values())
            assert set(r['label_reasons'])==set(r['labels']) and all(r['label_reasons'].values())
            assert not r['labels']['R4'] or g['tokens']>=4096
            r5=r['labels']['R5']
            label_rows.append(dict(task_id=task['task_id'],family_id=task['family_id'],item_id=task['item_id'],
                arm=task['arm'],**r['labels'],reasons=json.dumps(r['label_reasons'],ensure_ascii=False),
                quotes=json.dumps(r['quotes'],ensure_ascii=False),generation_sha256=sha(generation_path)))
        v=validity(all(checks.values()),r['scoreable'],g['cap_hit'],r5)
        result_rows.append(dict(task_id=task['task_id'],family_id=task['family_id'],item_id=task['item_id'],arm=task['arm'],
            answer_type=task['answer_type'],**v,cap_hit=g['cap_hit'],normal_stop=g['normal_stop'],tokens=g['tokens'],
            request_latency_seconds=g['request_latency_seconds'],extracted_outcome=r['extracted_outcome'],
            terminal_representation=r.get('terminal_representation',r['extracted_outcome']),
            scoreability_reason=r['reason'],commitment_quotes=json.dumps(r['quotes'],ensure_ascii=False),
            input_checks=json.dumps(checks),generation_path=str(generation_path),generation_sha256=sha(generation_path),
            raw_response=g['raw_decoded_response']))
    for filename,rows in [('stage12br_validation_results.parquet',result_rows),('stage12br_pathology_labels.parquet',label_rows)]:
        assert not (ROOT/filename).exists()
        pd.DataFrame(rows).to_parquet(ROOT/filename,index=False)
    decision=gate({a:[r for r in result_rows if r['arm']==a] for a in 'ENO'})
    freq={a:{f'R{i}':sum(r[f'R{i}'] for r in label_rows if r['arm']==a) for i in range(1,6)} for a in 'NO'}
    decision.update(at=now(),correctness_opened=False,bottleneck_estimates='NOT_ESTIMATED',pathology_frequencies=freq,
        manifest_sha256=sha(ROOT/'stage12br_validation_manifest.json'),decisions_sha256=sha(decisions_path),
        old_artifacts_unchanged=len(old_hashes),full_profiling_launched=False,requires_separate_authorization=True)
    save(ROOT/'stage12br_validation_decision.json',decision)
    resource=account('final',final=True)
    table='| Arm | Input valid | Scoreable | Truncated before outcome | Cap after outcome | Normal stop |\n|---|---:|---:|---:|---:|---:|\n'
    for a in 'ENO':
        s=decision['summaries'][a]
        table+=f'|{a}|{s["INPUT_VALID"]}/12|{s["SCOREABLE"]}/12|{s["TRUNCATED_BEFORE_OUTCOME"]}/12|{s["cap_after_outcome"]}/12|{sum(r["normal_stop"] for r in result_rows if r["arm"]==a)}/12|\n'
    pathology='| Arm | R1 repetition | R2 reopening | R3 nonconvergence | R4 long advancing | R5 terminal ambiguity |\n|---|---:|---:|---:|---:|---:|\n'
    for a in 'NO':pathology+='|'+a+'|'+'|'.join(f'{freq[a][f"R{i}"]}/12' for i in range(1,6))+'|\n'
    cap_table='| Capped response | Classification | Output-only rationale |\n|---|---|---|\n'
    for r in result_rows:
        if r['cap_hit']:
            classification='Cap after scoreable outcome' if r['cap_after_outcome'] else 'Truncated before scoreable outcome'
            cap_table+=f'|{r["task_id"]}|{classification}|{r["scoreability_reason"]}|\n'
    text=f'''# Stage12B-R pathology-aware validity repair

Decision: **{decision['decision']}**. This validates input integrity and scoreability only; task/evidence correctness remains unopened and bottleneck proportions are not estimated.

Fresh validation IDs: {', '.join(m['validation_ids'])}. Exclude the original 12 development cases; rank the remaining 49 by SHA256(`stage12br-validation-v1|family_id`), choose the first 5 multiple-choice and 7 open-ended families, and merge in hash order. Selection used only identity and answer type. The cohort, rules, pathology guide, and exact 36 copied requests were hashed before generation. Manifest SHA256: `{sha(ROOT/'stage12br_validation_manifest.json')}`.

E is the image-present evidence probe; N is native image-plus-question Instruct; O is the image-free Equal-Evidence Oracle.

{table}
Each arm must have 12/12 input-valid, at least 10/12 scoreable, and at most 1/12 pre-outcome truncation. No repetition threshold. Inputs were verified against exact frozen tasks, image hashes/multimodal payloads, oracle text, and the inherited 61-family source-only oracle review. No prompt/model/runtime/cap/seed change. All {len(old_hashes)} snapshotted Stage12B artifacts remain unchanged.

{cap_table}
Cap boundaries were reviewed semantically against the prospectively frozen rules. A still-committed answer does not require a correct or convergent derivation. Conversely, an earlier candidate does not suffice when later incompatible terminal answers remain unresolved. Complete traces and exact quotes support these distinctions.

{pathology}
Labels overlap and cover 24 N/O outputs. R1–R4 do not exclude otherwise scoreable outcomes; R5 is also unscoreable. Long advancing means at least 4096 tokens plus semantic progress, never merely length. One-agent semantic annotation used complete raw traces and supporting quotes. For the four capped traces, exact duplicate paragraphs were collapsed losslessly for review, with all unique text, offsets, duplicate maps, and original-order endings preserved. There is no independent inter-rater reliability claim. These small-set frequencies are technical-validation descriptions, not scientific prevalence or causal attribution.

All 36 raw outputs/token IDs are preserved; [full response pages](../../../reports/stage12br/v1/index.md). Validation parquet includes raw text and output-only extracted outcomes, never correctness. Pathology parquet preserves per-family labels/reasons/quotes. Annotation details: `audit/manual_validation_decisions.json`.

Allocated GPU use: {resource['allocated_gpu_hours']:.6f} GPU-hours including startup/teardown, against a target below 0.6 and a hard maximum of 1.0. Jobs: {', '.join(r['slurm_job_id']+'/'+r['node']+'/'+r['status'] for r in resource['jobs'])}. All stage GPU allocations released. No installs/downloads. The original 4B BF16/vLLM recipe was reused.

Full 61-family Stage12B scientific profiling was not launched. Section 21 requires separate authorization; any future authorized profiling must retain the frozen validity rule, original 61 families/157 facts, P1–P6/B1–B4 definitions, and planned sensitivity reports excluding the original 12 and all 24 technical cases. No correctness, bottleneck proportions, CoT, Thinking, or follow-on experiment here. Repetition causes remain unresolved.

{ENDING[decision['decision']]}
'''
    with (ROOT/'stage12br_summary.md').open('x') as f:f.write(text)
    expected=['stage12br_pathology_aware_validity_spec.md','stage12br_validation_manifest.json','stage12br_validity_rules.json',
        'stage12br_pathology_annotation_guide.md','stage12br_validation_results.parquet','stage12br_pathology_labels.parquet',
        'stage12br_validation_decision.json','stage12br_resource_accounting.json','stage12br_summary.md']
    save(ROOT/'audit/closure_validation.json',dict(at=now(),passed=True,n_calls=36,n_pathology_rows=24,
        correctness_opened=False,old_artifacts_preserved=len(old_hashes),all_stage_allocations_released=True,
        artifacts={name:sha(ROOT/name) for name in expected},review_code={str(p):sha(p) for p in [Path(__file__),Path('scripts/stage12br/review.py')]}))
    print(json.dumps(decision,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('decisions');main(p.parse_args().decisions)
