"""Synthesize the immutable census screen and historical evidence audits."""
from __future__ import annotations

import collections
import csv
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from scripts.thinking_math_failure_audit.analyze import (
    ROOT, OUT, SEED, DRAWS, VERSIONS, FLAG_PATTERNS, read_json, read_rows,
    save_json, save_csv, status_counts, interval, pair_transitions, evidence_state, sha,
)


def csv_rows(path):
    with Path(path).open() as f:
        return list(csv.DictReader(f))


def pct(x):
    return 'NA' if x is None else f'{100*float(x):.1f}%'


def rate_cell(r):
    return f"{r['wrong']}/{r['scored']} = {pct(r['wrong_rate'])} [{pct(r['ci_low'])}, {pct(r['ci_high'])}]"


def main():
    assert read_json(OUT/'validation.json')['complete']
    summary=read_json(OUT/'summary.json')
    rows=[r for r in read_rows(ROOT/'outputs/stage14b/scoring/scored_outputs.jsonl') if r['model']=='T']
    screens={r['task_id']:r for r in read_rows(OUT/'trace_screens.jsonl')}
    main_native=[r for r in rows if r['condition']!='evidence']
    mv=[r for r in main_native if not r['version']]
    verse=[r for r in main_native if r['version']]
    byid={r['task_id']:r for r in main_native}
    families={r['problem_index']:r for r in read_json(ROOT/'outputs/stage14a/v1/stage14a_mathverse788_family_manifest.json')['rows']}
    annotations={r['item_id']:r for r in read_json(ROOT/'outputs/stage14a/v1/stage14a_mathvision_e_star_annotations.json')['rows']}
    audit={r['item_id']:r for r in csv_rows(ROOT/'outputs/stage14d0_answer_evidence_supplement_v1/family_evidence_status.csv') if r['model']=='T'}
    evidence_followups={r['item_id']:r for r in csv_rows(OUT/'evidence_followups.csv') if r['replicate']=='0'}
    groups=csv_rows(OUT/'question_type_failure_rates.csv')
    subject_rows=sorted([r for r in groups if r['dataset']=='MATH-Vision' and r['dimension']=='subject'],key=lambda r:float(r['wrong_rate']),reverse=True)
    features=csv_rows(OUT/'source_feature_failure_rates.csv')

    # Existing source-review notes explicitly identify these issues. No gold is corrected.
    key_issue_ids={'90','91','144','145','622','629','720','728'}
    unit_issue_ids={'681','709','727'}
    note_issues=[]
    for item in sorted(key_issue_ids|unit_issue_ids,key=int):
        note_issues.append(dict(item_id=item,classification='existing_review_key_conflict' if item in key_issue_ids else 'existing_review_unit_conflict',
            existing_review_note=families[item]['review_note'],
            source='outputs/stage14a/v1/stage14a_mathverse788_family_manifest.json',
            score_change=False))
    note_issues.append(dict(item_id='2925',dataset='MATH-Vision',classification='new_source_gold_candidate_for_human_review',
        existing_gold='45^2',native_answer='45',score_change=False,
        evidence='Original task specifies right angle at A, adjacent lengths 15 and 24, and three side midpoints. The saved response derives 45; the frozen grader compares to literal 45^2. This is a source/gold inconsistency candidate, not automatically a model reasoning error.'))
    save_json(OUT/'source_gold_issue_notes.json',note_issues)

    # Main native inventory includes every scored failure and separately every unscorable output.
    failure_rows=[]
    for r in main_native:
        if r['status']=='CORRECT':continue
        s=screens[r['task_id']]; meta=r['source_metadata'];a=audit.get(r['item_id']) if not r['version'] else None
        e=evidence_followups.get(r['item_id']) if not r['version'] else None
        failure_rows.append(dict(dataset='MathVerse' if r['version'] else 'MATH-Vision',task_id=r['task_id'],
            item_id=r['item_id'],family_id=r['family_id'],version=r['version'],status=r['status'],
            subject=meta['subject'],question=meta['prompt'],image_path=meta['image'],gold=meta['gold_answer'],answer=r['answer'],
            tokens=r['tokens'],cap_hit=r['cap_hit'],
            evidence_audit=evidence_state(a['last_state']) if a else 'NO_SOURCE_VALIDATED_EVIDENCE_AUDIT',
            audit_panel=a['panel'] if a else None,e_star_status=e['evidence_status'] if e else None,
            image_expected=r['version']!='Text Only',
            image_unavailable_phrase=bool(s['lexical_flags']['image_unavailable_statement']),
            template_phrase=bool(s['lexical_flags']['template_language']),
            source_review_note=families[r['item_id']]['review_note'] if r['version'] else None,
            known_source_issue_note=r['item_id'] in key_issue_ids|unit_issue_ids if r['version'] else r['item_id']=='2925',
            generation_path=s['generation_path'],generation_sha256=s['generation_sha256'],input_path=s['input_path']))
    assert sum(r['status']=='WRONG' for r in failure_rows)==2303
    save_csv(OUT/'main_native_failure_cases.csv',failure_rows)
    coverage=collections.Counter((r['dataset'],r['evidence_audit']) for r in failure_rows if r['status']=='WRONG')
    save_csv(OUT/'failure_evidence_coverage.csv',[dict(dataset=d,evidence_coverage=e,n=n) for (d,e),n in sorted(coverage.items())])

    # Scope lexical behavior by actual native modality. Text Only is a legitimate no-image arm.
    behavior=[];lengths=[];flag_strata=[]
    for dataset,rr in [('MATH-Vision',mv),('MathVerse',verse)]:
        scopes=['image_present'] if dataset=='MATH-Vision' else ['image_present',*VERSIONS]
        for scope in scopes:
            ss=[r for r in rr if r['version']!='Text Only'] if scope=='image_present' else [r for r in rr if r['version']==scope]
            for status in ['CORRECT','WRONG','UNSCORABLE']:
                zz=[r for r in ss if r['status']==status]
                for flag in FLAG_PATTERNS:
                    k=sum(bool(screens[r['task_id']]['lexical_flags'][flag]) for r in zz)
                    early=sum(any(m['start'] < screens[r['task_id']]['raw_characters']/4 for m in screens[r['task_id']]['lexical_flags'][flag]) for r in zz)
                    behavior.append(dict(dataset=dataset,scope=scope,status=status,flag=flag,n=len(zz),flagged=k,
                        fraction=k/len(zz) if zz else None,flagged_first_quarter=early,
                        interpretation='Literal lexical candidate; not proof of image neglect. Text Only legitimately lacks an image.'))
            if scope=='image_present':
                for status in ['CORRECT','WRONG','UNSCORABLE']:
                    zz=[r for r in ss if r['status']==status]
                    ts=[r['tokens'] for r in zz]
                    lengths.append(dict(dataset=dataset,status=status,n=len(zz),median_tokens=float(np.median(ts)) if ts else None,
                        q25=float(np.quantile(ts,.25)) if ts else None,q75=float(np.quantile(ts,.75)) if ts else None,
                        cap_hits=sum(r['cap_hit'] for r in zz)))
                for lo,hi,label in [(0,2048,'0-2048'),(2049,8192,'2049-8192'),(8193,32768,'8193-32768'),(32769,10**9,'32769+')]:
                    for status in ['CORRECT','WRONG']:
                        zz=[r for r in ss if r['status']==status and lo<=r['tokens']<=hi]
                        flag_strata.append(dict(dataset=dataset,token_bin=label,status=status,n=len(zz),flagged=sum(bool(screens[r['task_id']]['lexical_flags']['image_unavailable_statement']) for r in zz)))
    save_csv(OUT/'trace_behavior_by_modality.csv',behavior)
    save_csv(OUT/'completion_and_length.csv',lengths)
    save_csv(OUT/'image_denial_length_strata.csv',flag_strata)

    strict_denials=[]
    for dataset,rr in [('MATH-Vision',mv),('MathVerse',[r for r in verse if r['version']!='Text Only'])]:
        for status in ['CORRECT','WRONG','UNSCORABLE']:
            ss=[r for r in rr if r['status']==status]
            selected=[]
            for r in ss:
                matches=[m for m in screens[r['task_id']]['lexical_flags']['image_unavailable_statement']
                         if any(noun in m['quote'].lower() for noun in ['image','diagram','picture','figure'])
                         and m['quote'].lower().startswith(('i ','we '))]
                if matches:selected.append(dict(task_id=r['task_id'],matches=matches))
            strict_denials.append(dict(dataset=dataset,status=status,n=len(ss),flagged=len(selected),
                fraction=len(selected)/len(ss) if ss else None,records=selected,
                definition='Subset of original screen: explicit I/we inability statement naming image/diagram/picture/figure. Excludes pronoun-only and missing-segment phrases; remains lexical, not causal.'))
    save_json(OUT/'strict_named_image_denial_sensitivity.json',strict_denials)

    candidates=[]
    for r in main_native:
        s=screens[r['task_id']]
        if s['lexical_flags']['image_unavailable_statement']:
            candidates.append(dict(task_id=r['task_id'],dataset='MathVerse' if r['version'] else 'MATH-Vision',
                item_id=r['item_id'],version=r['version'],status=r['status'],tokens=r['tokens'],
                image_expected=r['version']!='Text Only',matches=s['lexical_flags']['image_unavailable_statement'],
                generation_path=s['generation_path'],input_path=s['input_path']))
    save_csv(OUT/'text_reliance_screen_candidates.csv',candidates)

    # Verify saved inputs of every main image-present denial candidate. This does not certify attention/use.
    def verify_input(c):
        p=ROOT/c['input_path'];inp=read_json(p)
        receipt=read_json(p.parent/'result.json')
        assert sha(p)==receipt['input_sha256'],c['task_id']
        return dict(task_id=c['task_id'],input_path=c['input_path'],input_sha256=sha(p),
            expected_image=True,image_present=inp['image_present'],prepared_image_sizes=inp.get('prepared_image_sizes'),
            prepared_image_pixel_sha256=inp.get('prepared_image_pixel_sha256'),
            matches=c['matches'])
    image_candidates=[c for c in candidates if c['image_expected']]
    with ThreadPoolExecutor(max_workers=4) as pool:
        verified=list(pool.map(verify_input,image_candidates))
    save_json(OUT/'image_denial_input_receipt_check.json',dict(records=verified,
        n=len(verified),all_saved_inputs_image_present=all(x['image_present'] for x in verified),
        interpretation='Checks saved transport/preprocessing receipts, not whether internal reasoning used the visual tokens.'))

    # Fine-grained evidence: reuse original R/F results, never pool for prevalence.
    hist=[r for r in csv_rows(ROOT/'outputs/stage14d0_answer_evidence_supplement_v1/answer_by_evidence_crosstab.csv') if r['model']=='T']
    save_csv(OUT/'historical_thinking_evidence_crosstabs.csv',hist)
    diff=[r for r in csv_rows(ROOT/'outputs/stage14d0_visual_difficulty/v2/difficulty_by_model_error.csv') if r['model']=='T' and r['stratum']=='ALL']
    save_csv(OUT/'historical_thinking_source_difficulty.csv',diff)
    align=[r for r in read_rows(ROOT/'outputs/stage14d0/annotations/passB_Estar_atom_alignment.jsonl') if r['model']=='T' and r['source_QC']=='SOURCE_CHECKED']
    mechanisms=[]
    for panel in ['R','F']:
        for typ in sorted({t for r in align for t in r['evidence_types']}):
            eligible=[r for r in align if r['panel']==panel and typ in r['evidence_types']]
            for status in ['CORRECT','WRONG','UNSCORABLE']:
                ss=[r for r in eligible if r['final_answer_outcome_metadata']['native']==status]
                mechanisms.append(dict(panel=panel,evidence_type=typ,native_status=status,
                    family_opportunities=len({r['family_id'] for r in ss}),source_subfacts=len(ss),
                    families_with_explicit_error=len({r['family_id'] for r in ss if r['last_claim_state'] in ['STATED_INCORRECT','MISBOUND']}),
                    explicit_error_subfacts=sum(r['last_claim_state'] in ['STATED_INCORRECT','MISBOUND'] for r in ss),
                    note='Overlapping historical source types; not a mutually exclusive failure-cause decomposition.'))
    save_csv(OUT/'historical_evidence_type_failures.csv',mechanisms)

    # Additional sensitivity removes only documented source-note conflicts, without changing official scores.
    sensitivities=[]
    for label,excluded in [('official_no_exclusion',set()),('exclude_existing_key_notes',key_issue_ids),
                            ('exclude_existing_key_and_unit_notes',key_issue_ids|unit_issue_ids),
                            ('exclude_key_unit_and_explicit_TO_fail_note',key_issue_ids|unit_issue_ids|{'7'})]:
        for clean in [False,True]:
            rr=[r for r in verse if r['item_id'] not in excluded and (not clean or r['source_metadata']['clean_paired'])]
            for left,right in [('Text Dominant','Vision Only'),('Text Only','Vision Only')]:
                pp=pair_transitions(rr,left,right)
                sensitivities.append(dict(source_sensitivity=label,recorded_checks_pass_only=clean,left=left,right=right,n=pp['n'],counts=pp['counts'],
                    right_minus_left_error_pp=100*(pp['counts'].get('CORRECT__WRONG',0)-pp['counts'].get('WRONG__CORRECT',0))/pp['n']))
    save_json(OUT/'source_note_exclusion_sensitivity.json',sensitivities)

    # Modality transitions within subject, keeping all six cells nested in each original family.
    subjectpairs=[]
    for subject in sorted({r['source_metadata']['subject'] for r in verse}):
        for clean in [False,True]:
            rr=[r for r in verse if r['source_metadata']['subject']==subject and (not clean or r['source_metadata']['clean_paired'])]
            for left,right in [('Text Dominant','Vision Only'),('Text Only','Vision Only')]:
                p=pair_transitions(rr,left,right)
                subjectpairs.append(dict(subject=subject,checks_pass_only=clean,left=left,right=right,n=p['n'],counts=p['counts']))
    save_json(OUT/'modality_by_subject.json',subjectpairs)

    repeat_pair_intervals=[]
    for clean in [False,True]:
        rr=[r for r in verse if not clean or r['source_metadata']['clean_paired']]
        repeat_identity={r['item_id']:','.join(sorted(r['source_metadata']['source_repeat_problem_indices'],key=str)) for r in rr}
        for left,right in [('Text Dominant','Vision Only'),('Text Only','Vision Only')]:
            pairs=pair_transitions(rr,left,right)['pairs'];clusters=collections.defaultdict(list)
            for p in pairs:
                clusters[repeat_identity[p['item_id']]].append(int(p['right_status']=='WRONG')-int(p['left_status']=='WRONG'))
            totals=np.array([sum(v) for v in clusters.values()],dtype=float)
            sizes=np.array([len(v) for v in clusters.values()],dtype=float)
            n=len(clusters);w=np.random.default_rng(SEED).multinomial(n,np.full(n,1/n),size=DRAWS)
            boot=(w@totals)/(w@sizes)
            repeat_pair_intervals.append(dict(recorded_checks_pass_only=clean,left=left,right=right,
                pairs=len(pairs),source_repeat_clusters=n,estimate_pp=float(100*totals.sum()/sizes.sum()),
                ci_low_pp=float(100*np.quantile(boot,.025)),ci_high_pp=float(100*np.quantile(boot,.975))))
    save_json(OUT/'source_repeat_paired_intervals.json',repeat_pair_intervals)

    # Metadata volume vs subject, to expose the confounding behind the size gradient.
    size_subject=[]
    for r in mv:
        if r['item_id'] not in annotations:continue
        a=annotations[r['item_id']];n=sum(x.get('structured_subfact_count',0) or 0 for x in a['atom_metadata'] if x['atom_type']=='structured_layout')
        label='none' if n==0 else '1-4' if n<=4 else '5-9' if n<=9 else '10-19' if n<=19 else '20+'
        size_subject.append(dict(r,size_bin=label))
    sizetable=[]
    for subject in sorted({r['source_metadata']['subject'] for r in size_subject}):
        for size in ['none','1-4','5-9','10-19','20+']:
            ss=[r for r in size_subject if r['size_bin']==size and r['source_metadata']['subject']==subject]
            if ss:sizetable.append(dict(subject=subject,size_bin=size,**status_counts(ss)))
    save_csv(OUT/'structured_size_by_subject.csv',sizetable)

    report=['# What Thinking fails on in MATH-Vision and MathVerse', '',
      '**Completed 22 November 2026. Existing data only; zero model calls, zero GPUs, no changed scores.**', '',
      'The strongest shared pattern is difficulty reconstructing usable visual structure: topology/connectivity, spatial configuration, counting, transformations and structured layouts. There is also observable replacement of unresolved images by verbal assumptions or familiar templates. These are not the only failure regimes: local scale reading, source/entity binding, downstream reasoning, completion and source/gold defects are distinct.', '',
      '## Scope and what “all failures” means', '',
      f"All **{summary['total_thinking_records']:,}** Thinking generation records from the broad Stage14B main census and its fixed repeated-seed/equal-evidence followups were hash-checked and computationally screened. The primary native analysis is **7,768 r0 calls**: MATH-Vision 3,040 IDs and MathVerse 788 × six versions. It inventories every **2,303 scored native wrong output**, plus **26 unscorable MATH-Vision outputs**. Including repeated seeds, there are 3,417 native wrong and 35 native unscorable outputs; these are not additional independent questions.", '',
      '**This is not a new exhaustive semantic/image audit of 2,303 cases.** Every failure is enumerated and its full text screened. Source-validated evidence diagnoses exist for 156 MATH-Vision wrong outputs in the prior 300-family audit, and detailed source difficulty for R=150. Others retain UNKNOWN mechanism rather than receiving invented cause labels. Question-type rates compare failures with successful cases; they are not simply shares of the failure pile.', '',
      'Raw records: [all Thinking calls](../../outputs/thinking_math_failure_audit/v1/all_thinking_records.csv), [all main wrong/unscorable cases](../../outputs/thinking_math_failure_audit/v1/main_native_failure_cases.csv), [all-seed failure metadata and exact lexical excerpts](../../outputs/thinking_math_failure_audit/v1/failure_inventory.jsonl).', '',
      '## 1. Question types: MATH-Vision', '',
      'Wrong/scored excludes unscorable answers; all are shown separately. Intervals are retrospective 95% conservative-family cluster bootstrap intervals, 4,000 draws, seed 20261122. Multiple native IDs can share a family; family-equal sensitivities and every category are in the CSV. No multiplicity-adjusted or causal claim.', '',
      '| Native subject | Wrong / scored, rate [95% CI] | Unscorable | Family clusters |', '|---|---|---:|---:|']
    for r in subject_rows:report.append(f"| {r['level']} | {rate_cell(r)} | {r['unscorable']} | {r['clusters']} |")
    report += ['',
      'Topology has only 23 questions and is a sparse extreme. Descriptive geometry, counting, graph theory, combinatorial geometry and transformations form a broader, less sparse difficulty pattern. Subject names are benchmark metadata, not verified global/local labels. Area problems contribute many failures because there are 500 of them; their per-question error rate is lower than several structural categories.', '',
      'Native difficulty labels do not produce a monotonic error curve: difficulty 1 has 112/236 scored wrong (47.5%), versus 35–36% at levels 2–5. This is an unadjusted task-mixture observation. Open-ended and multiple-choice scored errors are similar (36.6% versus 36.2%); completion missingness differs. Full topic-cue, difficulty and answer-format tables are supplied in `question_type_failure_rates.csv`. Lexical topic cues are nonexclusive retrieval tags and do not certify source complexity.', '',
      '## 2. Beyond global/local: structured information burden', '',
      'The frozen source-only E*-eligible subset contains 1,000 families. These rates are final-answer errors, not visual-acquisition errors. They describe this selected subset, not the complete benchmark.', '',
      '| Frozen source feature | Value | Wrong / scored, rate [95% CI] |', '|---|---|---|']
    for r in features:
        if r['feature'] in ['structured_layout','structured_subfacts','requires_spatial_relation','requires_graph_table_reading','requires_diagram_label_reading']:
            report.append(f"| {r['feature']} | {r['level']} | {rate_cell(r)} |")
    report += ['',
      '**A useful additional pattern is the amount of structure to preserve.** Scored errors rise from 32.7% for structured objects with 1–4 recorded internal subfacts, to 43.2% for 5–9, 64.1% for 10–19 and 66.3% for 20+. Counting a whole grid/table/chain as one primary E* atom does not make it one simple datum. Primary atom count itself has no comparable monotonic curve.', '',
      'Internal subfact sizes are heterogeneous annotation units, not standardized information bits. Size, subject, topology and source eligibility are correlated; the gradient is unadjusted and does not prove a memory-capacity mechanism. `structured_size_by_subject.csv` exposes the subject composition. Requiring label reading alone is not uniformly harder: its final-error rate is lower than the complementary group. Do not infer that tiny text is the dominant problem.', '',
      '## 3. What the existing source audit actually establishes', '',
      'R is a source-selected 150-family panel; F is an additional outcome-enriched 150-family panel. Source-valid required E* facts are compared with explicit native statements. Missing, vague and unstable statements are unobservable/ambiguous, never proven acquisition failures.', '',
      '| Panel; Thinking native wrong | All required facts explicitly correct | At least one explicit required-source error | No explicit error, incomplete/ambiguous |', '|---|---:|---:|---:|',
      '| R: 69 wrong | 5 (7.2%) | 50 (72.5%) | 14 (20.3%) |',
      '| F: 87 wrong | 15 (17.2%) | 50 (57.5%) | 22 (25.3%) |',
      '| Combined, descriptive only: 156 wrong | 20 (12.8%) | 100 (64.1%) | 36 (23.1%) |', '',
      'R weighted explicit-error share among wrong answers is 72.4% [61.7, 82.5]; all-correct 7.3% [1.6, 13.8]; incomplete/ambiguous 20.3% [11.3, 30.3]. Combined counts cannot be extrapolated as census prevalence. The source audit also contains explicit errors in 27 correct Thinking outputs, so a correct final is not a certificate of faithful source statements.', '',
      'In the existing R difficulty extension, Thinking weighted explicit wrong/misbound evidence coverage is **18.88% for global-required** source facts, **14.93% for local-plus-global**, and **4.16% for local-sufficient**. Global-required minus local-sufficient is **+14.72 pp [7.94, 21.76]**. These are family-weighted subfact outcomes, not final-answer error rates. The extension uses 979 eligible facts after seven additional uncertainty exclusions; the table above retains the original source-valid audit definition. Do not merge their denominators.', '',
      'Other supported distinctions include scale/quantity reading, entity-to-value binding, topology/connectivity and coordinate-frame use. Counting and operation-specific point estimates are exploratory; visual-operation depth did not have a reliable monotonic effect, and tiny-text difficulty was not adequately represented. The current source annotations do not support a census claim about tiny text, distractor attention or pure perception.', '',
      'Pre-answer sensitivity is retained in `historical_thinking_evidence_crosstabs.csv`: it uses the first anchored statement before the existing answer boundary, not the last pre-answer evidence state. Many facts become unobservable in that view. Whole-output last-state evidence may include final exposition, so it does not certify acquisition timing.', '',
      '## 4. Text reliance, imagined diagrams and the Math Blind hypothesis', '',
      'The external [Math Blind / MATHEMETRIC project](https://vi-ocean.github.io/projects/MATHEMETRIC/) reports weaknesses in diagram perception and textual shortcuts. It motivates checking our traces; it is not evidence about these Qwen3-VL-4B generations. It is distinct from our BlindTest line-intersection representation experiment.', '',
      'We searched exact full-output text for image-unavailability claims, description/text references, explicit assumption language and familiar-template language. Each match preserves Unicode character offsets and context. These are lexical candidates, not semantic verdicts: assumptions can be legitimate, a description can be correct, and a model can claim blindness despite having image tokens.', '',
      '| Image-present native outputs | Image-unavailability phrase in wrong | Same phrase in correct |', '|---|---:|---:|']
    for dataset in ['MATH-Vision','MathVerse']:
        ss={r['status']:r for r in behavior if r['dataset']==dataset and r['scope']=='image_present' and r['flag']=='image_unavailable_statement'}
        report.append(f"| {dataset} | {ss['WRONG']['flagged']}/{ss['WRONG']['n']} ({pct(ss['WRONG']['fraction'])}) | {ss['CORRECT']['flagged']}/{ss['CORRECT']['n']} ({pct(ss['CORRECT']['fraction'])}) |")
    report += ['',
      f"Every one of the **{len(verified)}** image-present main denial candidates has a saved image-present input receipt: **{all(x['image_present'] for x in verified)}**. Exact preprocessing sizes/hashes are preserved in `image_denial_input_receipt_check.json`. This rules out absent image transport in those saved receipts; it does not demonstrate visual-token use or exclude other runtime issues. Text Only is excluded from this image-present table because no-image statements are legitimate there.", '',
      'MATH-Vision wrong traces also contain template phrases in 603/1,097 and assumption phrases in 957/1,097. Neither is an error label. Wrong traces are much longer, giving more opportunities for these phrases; length-stratified and early-first-quarter counts are retained. These associations do not isolate a causal effect of text reliance.', '',
      'The broad search includes pronoun-only “I cannot see it” and occasional false positives such as a diagram “missing a segment.” A stricter named-image sensitivity retains only explicit I/we inability statements naming image/diagram/picture/figure: MATH-Vision **178/1,097 wrong (16.2%) versus 119/1,917 correct (6.2%)**; image-present MathVerse **33/969 wrong (3.4%) versus 55/2,971 correct (1.9%)**. These remain self-reported text, not certified image-neglect diagnoses. The broader screen and strict subset are both preserved.', '',
      '**Three different phenomena must remain separate:** (1) a textual premise supplied by the user; (2) a model-generated textual surrogate for an unresolved picture; (3) valid algebra after correct visual facts. Cases 9 and 32 explicitly appeal to typical/standard diagrams despite image input. Case 2997 substitutes a rectangle for the source trapezoid. These support an observable template-substitution hypothesis; they do not prove that attention never reached the image. There is no controlled text–image conflict experiment here that could identify a universal preference for prompt text over pixels.', '',
      '## 5. MathVerse: text availability matters, but source validity changes the comparison', '',
      '| Version | Thinking wrong / 788 | Error rate |', '|---|---:|---:|']
    for version in VERSIONS:
        rr=[r for r in verse if r['version']==version];cc=status_counts(rr)
        report.append(f"| {version} | {cc['wrong']} | {pct(cc['wrong_rate'])} |")
    report += ['',
      'Subject-wise Vision Only errors are Plane Geometry 131/510 (25.7%), Functions 49/159 (30.8%), and Solid Geometry 45/119 (37.8%). Within these categories, angle/length binding, graph/function interpretation and 3D geometry are useful review targets; broad subject metadata do not establish which operation caused each error.', '',
      '| Paired comparison | Families | Left correct → right wrong | Left wrong → right correct | Right-minus-left error, pp [95% CI] |', '|---|---:|---:|---:|---|']
    for p in read_json(OUT/'modality_transitions.json'):
        if p['left'] not in ['Text Dominant','Text Only'] or p['right']!='Vision Only':continue
        label=('Recorded checks pass; ' if p['clean_only'] else 'Census; ')+p['left']+' → '+p['right']
        report.append(f"| {label} | {p['n']} | {p['counts'].get('CORRECT__WRONG',0)} | {p['counts'].get('WRONG__CORRECT',0)} | {p['right_minus_left_error_pp']:+.2f} [{p['ci_low_pp']:+.2f}, {p['ci_high_pp']:+.2f}] |")
    report += ['',
      'On all 788 families, Text Only is not better than Vision Only; in the 350-family recorded-checks-pass subset, Text Only is 330/350 correct versus Vision Only 280/350. Thus valid text-supplied geometry can be substantially easier than extracting it from images. That supports an evidence-interface bottleneck, not the claim that every image-present failure ignored the image. Vision Only also contains the question/choices in the raster, so it adds reading/formatting demands beyond diagram perception.', '',
      'The recorded clean checks have limits: visual sufficiency review specifically targeted VD/VO, not a guarantee that every intermediate version preserves all constraints. For example, family 59 Vision Intensive drops parallelism/bisection without visual replacement. More seriously, family 7 has `text_only_sufficient=PASS` but its detailed review says “Text-only sufficiency FAILS.” Family 90 passes literal gold consistency despite a separately documented geometric key conflict; family 629 has the unrelated native gold “Bugs Bunny.” Thus the 350-family checkbox subset is not a new certification of full semantic validity. The source-note exclusion sensitivity retains the main direction without overwriting historical labels; only explicitly identified note issues are excluded, not an exhaustive new source audit.', '',
      'Across six versions, 381 families are all-correct, 75 all-wrong and 332 mixed. All-wrong is not proof of a downstream mathematical bottleneck: family 90 is a counterexample with a documented gold conflict. Source-repeat clustering reduces the 788 family identifiers to 772 clusters; this changes uncertainty modestly and does not create new observations.', '',
      '## 6. Evidence-supply followups distinguish opportunity from persistent failure', '',
      'Within the 1,000-family source-eligible MATH-Vision cohort, Thinking has 420 native wrong answers. Of these, **306 become correct with E***, **110 remain wrong**, and **4 are unscorable with E***. The scored-followup rescue is **306/416 = 73.6%**; over all 420 native-wrong cases, observed rescue is 72.9%. There are also 30 native-correct → evidence-wrong regressions and one evidence-unscorable followup among native-correct cases.', '',
      'This is strong evidence that usable source-derived textual evidence often helps this subset. It changes representation, binding and reasoning context, so it cannot identify a pure acquisition-failure fraction. Persistent E* failures require examining reasoning, source validity and output behavior; they are not automatically arithmetic errors. Repeated seeds preserve 88/120 and 89/119 scored-followup rescue, without adding independent families.', '',
      '## 7. Completion and downstream behavior', '',
      '| Image-present dataset | Native status | n | Median tokens | IQR | Cap hits |', '|---|---|---:|---:|---|---:|']
    for r in lengths:
        if not r['n']:continue
        report.append(f"| {r['dataset']} | {r['status']} | {r['n']} | {r['median_tokens']:,.0f} | {r['q25']:,.0f}–{r['q75']:,.0f} | {r['cap_hits']} |")
    report += ['',
      'Long uncertain deliberation is common, but duration and “wait” counts are not causal diagnoses. An exact repeated-window screen finds no ≥10% verbatim 32-word-window duplication in wrong main outputs; this does not exclude semantic loops such as case 32, where the wording varies while the same alternatives recur.', '',
      'Some wrong outputs have all minimal required source facts correct. Existing audit examples distinguish downstream construction/use mistakes (1118), formula/repair failure after source restatement (2045), and an extra full-grid coordinate error outside minimal E* (2239). These must not all be labelled missing visual evidence. Conversely, a correct minimal E* reference does not certify every other visual statement in the trace.', '',
      '## 8. Source/gold and measurement failures', '',
      'Known MathVerse review notes describe key conflicts in 90, 91, 144, 145, 622, 629, 720 and 728, plus unit conflicts in 681, 709 and 727. Original raw scores remain unchanged. A newly inspected MATH-Vision example, 2925, derives 45 from the stated right triangle and midpoints, but the archived gold is literal `45^2`, producing WRONG under the frozen scorer. This is flagged for human source/gold review, not silently repaired. No census-wide corrected accuracy is claimed.', '',
      'A wrong benchmark label is therefore not automatically a model acquisition failure. Existing source annotations and E* can also be incomplete or imperfect. The analysis keeps these measurement issues visible rather than forcing all cases into perceptual or reasoning categories.', '',
      '## 9. Failure taxonomy and conclusion', '',
      '| Regime | What supports it here | What remains unknown |', '|---|---|---|',
      '| Global topology / structural reconstruction | High topology, graph, spatial/transformation errors; R global-context evidence contrast | Whether a particular crop/global intervention would repair it |',
      '| Structured information burden | Strong internal-size gradient in the frozen source subset | Standardized information volume and subject-adjusted mechanism |',
      '| Local source reading / entity binding | Exact source-audited wrong scales, endpoints, labels and source bindings | Census-wide frequency outside reviewed source families |',
      '| Template or verbal-surrogate substitution | Exact traces replace unresolved diagrams with familiar configurations, sometimes denying image access despite transport | Causal attention/use, genuine text–image conflict preference |',
      '| Incomplete/ambiguous evidence | Existing source audit retains unmentioned/uncertain facts | Latent acquisition; absence of mention is not failure |',
      '| Downstream state/construction/computation | Wrong finals with correct minimal evidence and detailed trace case notes | Pure downstream prevalence; E* may omit other source facts |',
      '| Uncertainty / completion | Long varying reconsideration, cap/unscorable records | Whether additional tokens or source rereading would improve it |',
      '| Source/gold/representation defects | Existing source notes and the 2925 gold discrepancy candidate | Full human-validated corrected benchmark labels |', '',
      '**Assessment:** the data support a compound problem—forming the right visual structure, preserving/binding its details, and preventing an unresolved picture from being replaced by a convenient verbal template. “The model just needs more reasoning” and “it always ignores images” are both too broad. The most informative next research question is whether a source-verified structural representation prevents these substitutions while preserving correct local facts. This analysis does not launch that experiment or resume the paused method-development work.', '',
      '## Artifacts and limits', '',
      'The [14-case source/output casebook](casebook_20261122.md) supplies exact references, quoted spans and limits, with complete raw traces linked. CSV/JSON artifacts preserve all main failures, repeated-seed followups, source flags, family clustering, ambiguity and lexical screens. Existing global/local numbers and source evidence judgments are single-AI retrospective annotations with prior exposure and no independent human reliability. New tables are exploratory; intervals include family resampling only. Full coverage means complete artifact inventory/screening, not 2,303 new manually certified causes.', '',
      '[Analysis plan](../../plan/thinking_math_failure_retrospective_20261122.md) · [Data validation](../../outputs/thinking_math_failure_audit/v1/validation.json) · [Source audit supplement](../../outputs/stage14d0_answer_evidence_supplement_v1/supplementary_report.md) · [Prior source difficulty](../../outputs/stage14d0_visual_difficulty/v2/report.md) · [Math Blind official repository](https://github.com/Vi-Ocean/MATHEMETRIC_Benchmark).', '',
      '**STOP. No follow-on experiment was run.**']
    reportdir=ROOT/'reports/thinking_math_failure_audit';reportdir.mkdir(parents=True,exist_ok=True)
    (reportdir/'thinking_failure_analysis_20261122.md').write_text('\n'.join(report)+'\n')
    (OUT/'report.md').write_text('\n'.join(report).replace('../../outputs/','../../').replace('../../plan/','../../../plan/').replace('(casebook_20261122.md)','(casebook.md)')+'\n')
    save_json(OUT/'prior_work_sources.json',dict(access_date='2026-11-22',sources=[
        {'title':'Math Blind: Failures in Diagram Understanding Undermine Reasoning in MLLMs','url':'https://vi-ocean.github.io/projects/MATHEMETRIC/','role':'External motivation, not evidence about our model outputs'},
        {'title':'Official MATHEMETRIC benchmark repository','url':'https://github.com/Vi-Ocean/MATHEMETRIC_Benchmark'},
        {'title':'Paper identifier','url':'https://arxiv.org/abs/2503.20745','note':'Project-page and repository contents verified; PDF fetch exceeded web-tool limit.'}]))
    save_json(OUT/'synthesis_validation.json',dict(main_wrong_cases=2303,main_unscorable_cases=26,
        image_denial_inputs_checked=len(verified),all_checked_inputs_image_present=all(x['image_present'] for x in verified),
        historical_source_fact_records=len(align),new_model_calls=0,new_score_changes=0,new_gpu_hours=0))
    print('Report written; input receipts checked:',len(verified),flush=True)


if __name__=='__main__':
    main()
