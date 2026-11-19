"""Publish the prespecified forced-contract stop, with no invented science results."""
import re
from pathlib import Path
import pandas as pd
from scripts.stage13c.execution import *
from scripts.stage13c.resources import account
from scripts.stage13c.extraction_notes import NOTES

RECOMMENDATION="Retain Stage 13A's confirmed post-evidence advantage as the strongest claim and do not expand the mechanism story."

def main():
    assert load(ROOT/'audit/stop_trigger.json')['decision']=='FORCED_TRACE_CONTRACT_BLOCKED'
    ledger=account('final_contract_stop');assert not ledger['active_jobs'] and ledger['allocated_gpu_hours_upper']<18
    tasks=load(ROOT/'audit/technical_buffer_tasks.json')['tasks'];reviews=[];receipts={};completed=[]
    for t in tasks:
        folder=ROOT/'generations'/t['task_id'];inp=load(folder/'input.json');fp=folder/'forced_receipt.json';f=load(fp)
        assert inp['task']==t and inp['task_sha256']==fingerprint(t) and not inp['image_present']
        assert not set([151652,151653,151655,151656]).intersection(t['prompt_token_ids'])
        assert t['chat_prompt'].endswith('<|im_start|>assistant\n<think>\n')
        assert f['forced_token_ids']==t['forced_token_ids']
        assert f['forced_decoding_step_count']==len(t['forced_token_ids'])==f['answer_generation_start_position']
        assert f['close_marker_position']==len(t['forced_token_ids'])-1 and f['one_token_per_step']
        r=dict(task_id=t['task_id'],family_id=t['family_id'],item_id=t['item_id'],condition=t['condition'],
            forced_reasoning_tokens=f['reasoning_token_count'],forced_decoding_steps=f['forced_decoding_step_count'],
            exact_token_contract=True,no_image=True,dummy_answer_leakage=False,
            input_sha256=sha(folder/'input.json'),receipt_sha256=sha(fp),complete=(folder/'result.json').exists(),
            scientific=False,correctness_graded=False)
        if r['complete']:
            result=load(folder/'result.json');g=load(folder/'generation.json');ids=g['generated_token_ids']
            assert result['generation_sha256']==sha(folder/'generation.json') and result['input_sha256']==sha(folder/'input.json')
            assert ids[:len(t['forced_token_ids'])]==t['forced_token_ids'] and t['open_id'] not in ids[len(t['forced_token_ids']):]
            assert g['prompt_token_ids']==t['prompt_token_ids'] and g['seed']==t['seed'] and g['tokens']==len(ids)
            cfg=load('outputs/stage13c/v1/audit/config_loader_repair_v1.json')
            assert g['sampling']==dict(cfg['models']['T']['recipe'],max_tokens=81920)
            closes=[i for i,x in enumerate(ids) if x==t['close_id']]
            violation=len(closes)>1
            # A second close is an objective witness; absence alone is not a semantic pass.
            evidence=None
            if violation:
                evidence='Second native </think> after unscripted deliberation; closing the first marker did not constrain subsequent reasoning.'
            elif t['item_id']=='2472':
                assert 'But wait!' in g['answer_text']
                evidence='Own-response review: computes a conflicting decomposition, then reconsiders it ("But wait!") and continues deriving before committing.'
            else:
                evidence='No second close; extended solution prose. Not certified as zero additional reasoning, and unnecessary to adjudicate after the witnessed gate failure.'
            r.update(tokens=len(ids),finish_reason=g['finish_reason'],cap_hit=g['cap_hit'],
                generated_tokens_after_forced_close=len(ids)-len(t['forced_token_ids']),close_positions=closes,
                extra_native_close=violation,unambiguous_continued_deliberation=violation or t['item_id']=='2472',
                no_additional_free_reasoning=False if violation or t['item_id']=='2472' else None,
                behavior_review=evidence,extra_tokens_before_second_close=closes[1]-closes[0]-1 if violation else None,
                generation_sha256=sha(folder/'generation.json'),request_latency_seconds=g['request_latency_seconds'])
            completed.append((t,g))
        else:
            r.update(status='INTERRUPTED_AFTER_FORCED_RECEIPT',no_additional_free_reasoning=None,
                reason='Cancelled after the contract stop; free suffix was not flushed. Not a cap hit or scientific failure.')
        reviews.append(r);receipts[str(fp)]=sha(fp)
    assert len(reviews)==8 and sum(r.get('extra_native_close',False) for r in reviews)>=1
    validation=dict(at=now(),passed=False,decision='FORCED_TRACE_CONTRACT_BLOCKED',technical_families=4,
        attempted_calls=8,completed_calls=len(completed),interrupted_calls=8-len(completed),
        exact_forced_receipts=8,extra_close_witnesses=sum(r.get('extra_native_close',False) for r in reviews),
        continued_deliberation_witnesses=sum(r.get('unambiguous_continued_deliberation',False) for r in reviews),
        rows=reviews,semantic_and_instruct_technical_checks='NOT_RUN_AFTER_CONTRACT_STOP',
        scientific_calls=0,review_scope='Own-response contract review, no correctness grading; same-agent QC.',
        interpretation='An exact first close marker and a ban on <think> reopening do not enforce zero free reasoning. No answer-only prompt, grammar, penalty or cap tuning was attempted.')
    save(ROOT/'stage13c_forced_trace_technical_validation.json',validation)
    drafts=[]
    for item,notes in NOTES.items():
        p=ROOT/'audit/source_packets'/f'{item}.json';source=load(p)
        drafts.append(dict(item_id=item,family_id=source['family_id'],source_packet_sha256=sha(p),
            draft_propositions=[dict(text=a,source_anchor=b,verification_note=c) for a,b,c in notes],
            status='DRAFT_NOT_QC_SEALED_NOT_USED_FOR_GENERATION'))
    save(ROOT/'stage13c_derived_state_extractions.json',dict(at=now(),status='DRAFT_PRESERVED_AT_TECHNICAL_STOP',
        scientific_D_sealed=False,rows=drafts,source_code_sha256=sha('scripts/stage13c/extraction_notes.py'),
        note='Source annotations were in progress alongside disjoint dummy-only technical validation. They were never intervention inputs. Not exhaustive, not final-QC certified, and not an authorized semantic cohort.'))
    save(ROOT/'stage13c_derived_state_audit.json',dict(at=now(),status='NOT_COMPLETED_CONTRACT_STOP',
        completed_before_scientific_generation=False,scientific_generation_started=False,
        eligible_semantic_families=None,correctness_labels_sealed=False,
        required_flags=['EXPLICIT_FINAL_PRESENT','ANSWER_COMMITMENT_PRESENT','GOLD_ANSWER_EQUIVALENT_PRESENT','QUESTION_RESTATEMENT_PRESENT','E_STAR_RESTATEMENT_PRESENT'],
        reason='Do not certify unfinished source drafts after stopping at the earlier forced-token contract gate. No intervention outcomes were used to select a scientific D.'))
    save(ROOT/'stage13c_dummy_token_sequences.json',dict(at=now(),phrase='Let me think.',
        status='TECHNICAL_BUFFER_SEQUENCES_ONLY',rows=[dict(task_id=t['task_id'],family_id=t['family_id'],condition=t['condition'],
        reasoning_token_ids=t['forced_token_ids'][:-1],native_close_id=t['close_id']) for t in tasks],
        semantic_control_sequences='NOT_MATERIALIZED_CONTRACT_STOP'))
    save(ROOT/'stage13c_seed_manifest.json',dict(at=now(),status='TECHNICAL_ONLY_SCIENCE_NOT_MATERIALIZED',tasks=tasks,
        scientific_tasks=[],scientific_formula='full SHA256(stage13c-v1|family_id|condition|replicate) integer modulo2**31, replicates0..4',
        technical_formula='same with namespace stage13c-v1-technical, replicate0',
        scientific_seeds_generated_or_used=False))
    columns=['task_id','family_id','item_id','condition','replicate','seed','correct','technically_valid','status']
    for name in ['thinking_compute','thinking_semantic','instruct_priming']:
        pd.DataFrame(columns=columns).to_parquet(ROOT/f'stage13c_{name}_results.parquet',index=False)
    families=[dict(family_id=r['family_id'],item_id=r['item_id'],status='NOT_RUN_CONTRACT_STOP',
        B=None,R=None,S=None,P_dummy=None,P_shuffle=None,P_base=None,scientific_calls=0)
        for r in load(ROOT/'stage13c_frozen24_manifest.json')['rows']]
    pd.DataFrame(families).to_parquet(ROOT/'stage13c_family_level_effects.parquet',index=False)
    not_estimated=dict(at=now(),status='NOT_ESTIMATED_CONTRACT_STOP',reason='No scientific calls; forced-token contract failed on disjoint technical cases.',
        scientific_effects=None,confidence_intervals=None,not_a_null_result=True)
    save(ROOT/'stage13c_missingness_bounds.json',dict(not_estimated,
        missingness_gate_reached=False,interrupted_technical_calls_are_not_scientific_missingness=True))
    save(ROOT/'stage13c_primary_inference.json',dict(not_estimated,bootstrap_executed=False,signals_evaluated=False))
    save(ROOT/'stage13c_scoring_audit.json',dict(at=now(),status='NOT_RUN_CONTRACT_STOP',new_correctness_graded=False,
        paired_scientific_labels_opened=False,technical_contract_review='Own-response marker/sequence receipts and deliberation witnesses only.',
        source_historical_correctness='Archived per plan, never used in cohort or replicate selection.',
        independent_rater_reliability_claimed=False))
    save(ROOT/'stage13c_decision.json',dict(at=now(),decision='FORCED_TRACE_CONTRACT_BLOCKED',
        authorized_stage_terminated_at_prespecified_gate=True,full_scientific_study_completed=False,
        scientific_conclusion='NOT_EVALUATED',recommendation=RECOMMENDATION,follow_on_launched=False))
    ledger.update(target_gpu_hours=14,technical_model_calls_attempted=8,technical_calls_completed=len(completed),
        technical_calls_interrupted=8-len(completed),startup_failed_jobs=2,scientific_calls=0,all_allocations_released=True,
        follow_on_launched=False,peak_memory_scope='Model/KV startup memory preserved in worker logs; no fabricated peak-memory metric.')
    ledger['receipts']={str(p):sha(p) for p in (ROOT/'workers').rglob('*.json')}
    save(ROOT/'stage13c_resource_accounting.json',ledger)
    report=Path('reports/stage13c/v1');(report/'responses').mkdir(parents=True,exist_ok=True)
    response_lines=['# Saved Stage13C technical responses','','No scientific responses or accuracy comparisons were generated. Complete token IDs and forced prefixes remain in raw JSON.','',
        '| Item | Condition | Forced reasoning tokens | Post-close tokens | Extra closing marker | Response |','|---|---|---:|---:|---|---|']
    bytid={r['task_id']:r for r in reviews}
    for t,g in completed:
        r=bytid[t['task_id']];p=report/'responses'/f"{t['task_id']}.md";raw=g['answer_text']
        fence='`'*max(4,1+max([len(x) for x in re.findall(r'`+',raw)],default=0))
        p.write_text('\n'.join(['# '+t['task_id'],'','Technical only; correctness not graded.',
            f"Forced reasoning tokens: {r['forced_reasoning_tokens']}. Close positions: {r['close_positions']}. Generated tokens after first close: {r['generated_tokens_after_forced_close']}.",'',
            f"[Full raw response and IDs](../../../../{ROOT}/generations/{t['task_id']}/generation.json) · [Forced-step receipt](../../../../{ROOT}/generations/{t['task_id']}/forced_receipt.json)",'',
            '## Frozen image-free input','',fence+'text',t['prompt'],fence,'','## Entire free continuation after forced close','',fence+'text',raw,fence,'']))
        response_lines.append(f"| {t['item_id']} | {t['condition']} | {r['forced_reasoning_tokens']} | {r['generated_tokens_after_forced_close']} | {r['extra_native_close']} | [Open](responses/{p.name}) |")
    response_lines+=['','The unfinished short2472 call was cancelled after the stop. Its input and exact17-step forced receipt are saved; its free suffix was not flushed. This is not a cap hit or a model failure.']
    (report/'responses.md').write_text('\n'.join(response_lines)+'\n')
    history=load(ROOT/'audit/historical_preservation.json')['files']
    for p,h in history.items():assert sha(p)==h,p
    code=[]
    for cfg_path in [ROOT/'config.json',ROOT/'audit/config_loader_repair_v1.json']:
        for p,h in load(cfg_path)['source_sha256'].items():
            actual=Path(p)
            if sha(actual)!=h:actual=ROOT/'audit/code_before_loader_repair'/actual.name
            assert sha(actual)==h,(cfg_path,p)
            code.append(dict(config=str(cfg_path),original_path=p,verified_path=str(actual),sha256=h))
    lines=['# Stage13C — stopped at forced-reasoning contract validation','','Decision: **FORCED_TRACE_CONTRACT_BLOCKED**. The scientific mechanism study was not run.','',
        'The source-only24-family cohort, disjointtechnical4 and initial8 were sealed. All28 source traces use the first technically resolved Stage13A replicate, without correctness selection. Original Q+E*, 4B checkpoints, recipes and caps were preserved.',
        '',f'Technical execution:8 attempted short/long dummy calls; {len(completed)} normal-stop responses saved and {8-len(completed)} interrupted after the gate. All8 exact forced-token receipts pass:16-token short traces or source-length long traces, one token per autoregressive step with KV continuation, native closing token at the prescribed position, no forced-prefix prefill, no images.',
        '',f'However, {validation["extra_close_witnesses"]}/{len(completed)} completed outputs emit a second native </think> after thousands of free tokens. One further long2472 output shows explicit reconsideration without a second marker. Long1269 has no second marker and extended final-solution prose; no semantic no-reasoning pass is inferred from marker absence. These are technical-case observations, not a population-rate estimate.',
        '', '| Item / condition | Forced close position | Second close position | Free tokens before second close |','|---|---:|---:|---:|']
    for r in reviews:
        if r.get('extra_native_close'):lines.append(f"| {r['item_id']} / {r['condition']} | {r['close_positions'][0]} | {r['close_positions'][1]} | {r['extra_tokens_before_second_close']} |")
    lines += ['', 'For example, short2360 continues with “Wait, no. Let’s think more carefully” and repeated variable redefinitions after its forced close. Short1269 starts a fresh step-by-step derivation. The literal first-close and no-reopening-token constraints therefore do not enforce the required absence of additional free reasoning. The resulting short/long comparison would not isolate the intended amount of reasoning computation.',
        '', 'The plan requires stopping at this contract boundary. No scientific call, initial-eight missingness gate, native/semantic/Instruct technical extension, correctness scoring, paired inference or bootstrap was run. No prompt, answer grammar, sampling, penalty or cap search was attempted. The underlying cause of ignoring the semantic boundary is unresolved; the emitted behavior is directly observed.',
        '', 'Source-derived annotations for28families remain clearly marked drafts, not final leakage/QC certificates and never used as interventions. Required downstream artifacts explicitly record NOT_RUN/NOT_ESTIMATED; scientific result tables are empty, family effects are null. The five scientific figures are not estimable and were not fabricated. A standalone technical diagnostic figure is provided instead.',
        '', 'The first two Slurm jobs failed before any call because of a custom-processor loader delimiter error. The actual vLLM loader regression reproduced it; a one-character correction, versioned config and original source snapshots were preserved. The repeated run passed the mechanical token-step checks. This wiring issue is separate from the observed scientific-contract failure.',
        '', f'Resources: {ledger["allocated_gpu_hours_upper"]:.6f} allocated GPU-hours across4jobs; all released. {len(history):,} prior Stage12/13 files verified unchanged. Completed raw responses, interrupted input/forced receipt, logs, source traces, drafts and both code/config versions are preserved.',
        '', 'Exactly one recommendation: '+RECOMMENDATION,'','STOP. No follow-on launched.']
    with (ROOT/'stage13c_summary.md').open('x') as f:f.write('\n'.join(lines)+'\n')
    (report/'index.md').write_text((ROOT/'stage13c_summary.md').read_text()+'\n[Saved answers/reasoning](responses.md) · [Technical validation](../../../outputs/stage13c/v1/stage13c_forced_trace_technical_validation.json) · [Resources](../../../outputs/stage13c/v1/stage13c_resource_accounting.json)\n')
    required=['post_evidence_mechanism_spec.md','frozen24_manifest.json','technical4_manifest.json','source_trace_manifest.json','derived_state_extractions.json','derived_state_audit.json','dummy_token_sequences.json','seed_manifest.json','forced_trace_technical_validation.json','thinking_compute_results.parquet','thinking_semantic_results.parquet','instruct_priming_results.parquet','scoring_audit.json','family_level_effects.parquet','missingness_bounds.json','primary_inference.json','decision.json','resource_accounting.json','summary.md']
    save(ROOT/'audit/final_verification.json',dict(at=now(),artifacts={str(ROOT/('stage13c_'+name)):sha(ROOT/('stage13c_'+name)) for name in required},
        historical_files_unchanged=len(history),code_versions=code,scientific_calls=0,all_gpus_released=True,
        figures_status='Five scientific figures not estimable at technical gate; technical diagnostic only.',
        terminated_at_prespecified_gate=True,full_scientific_study_completed=False))
    print('FORCED_TRACE_CONTRACT_BLOCKED',len(completed),'complete',ledger['allocated_gpu_hours_upper'],'GPUh',len(history),'historical files preserved')

if __name__=='__main__':main()
