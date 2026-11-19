"""Prospective seals; never reads a Stage13D scientific output."""
import copy
from scripts.stage13d.execution import *
from scripts.stage13d.protocol import donor
from scripts.stage13c.extraction_notes import NOTES

SPEC='''# Stage13D prospective specification

The approved plan is authoritative. Exact Stage13C scientific24, technical4 and
first technically resolved source traces are reused, without outcome selection.
All Stage12/prior13 output/report/code hashes are preserved before new execution.
Stage13A Q+E* is unchanged and image-free. 4B checkpoints and model-specific native
recipes remain fixed. Instruct: temperature.7/top_p.8/top_k20/repetition1/presence1.5,
32768 output tokens. Buffer uses the pinned Thinking checkpoint; no stochastic
sampling occurs, so deterministic forced scoring has no temperature/penalty effect.
BF16 vLLM0.11/TP1/engine42/cacheoff, max_model_len128000; semantic batch18,
buffer batch4. No system/CoT/answer-only instruction. Ordinary native EOS for A.

Finalize source-derived compact propositions and source anchors before generation.
This is a source-grounded compact extraction, not exhaustive trajectory labeling.
Retain erroneous deductions; correctness is annotated separately. Exclude final
commitments, final-equivalent target conclusions, Q/E* restatements and speculative
planning. D is ordered by source occurrence. Same-agent source review and second
leakage pass are not independent-rater reliability. A family without identified
safe content remains in the24 manifest and MC buffer panel, but receives no A calls.

A uses BASE/DERIVED/DUMMY/SHUFFLED, five fresh seeds per family-condition. Seed is
the full prescribed SHA256 integer modulo2**31. BASE has exact Q+E* only; the three
context arms use the exact neutral wrapper in the plan. Dummy repeats/truncates
the exact fixed sentence to D's Instruct-token count (roundtrip verified). Donors
use minimum absolute length difference among other eligible scientific families,
then SHA256(stage13d-v1|target_id|donor_id). No donor balancing or accuracy criterion.
The initial8 are first8 safe families in the inherited Stage13C initial8 hash
ordering over24. This is frozen before outputs. >20% technical missingness in any
40-call A arm stops remaining PhaseA; PhaseB is independently gated.

B uses every fixed-MC family, canonical option letters in original order. Letter
tokenization must be singleton for the shared-logit implementation. Every output
token is forced one at a time:16 or sourceL dummy reasoning tokens, native close,
exact literal Final answer:, then the first option letter. At the candidate step,
raw-model full-vocabulary fp32 log_softmax is saved for ALL candidate letters before
forcing. Each singleton's teacher-forced likelihood has identical prior history;
vectorized scoring is exactly equivalent to separate singleton candidate branches.
The sampled output is deterministically the first letter for bookkeeping, never
a prediction. Request ends at that step; zero free model tokens, no future context.
No dummy prefix prefill, no prefix caching/speculation, same-request KV continuation.
Gold is used only in subsequent margin calculation, not logits selection.

Technical4 includes2MC and2open-ended. All4 validate short/long counts, prefix,
no-image and zero-free-token contracts. Open-ended technical cases use their frozen
gold value solely as a multi-token teacher-forcing probe, no invented distractors,
no scientific buffer inclusion or accuracy claim. All4 short probes are repeated
in identical batch order/shape; deterministic likelihood tolerance absolute1e-5,
fixed prospectively. Scientific B runs only after all checks pass. Buffer technical
failure yields IMMEDIATE_BUFFER_ASSAY_BLOCKED, and cannot stop semantic work.

A outcomes are own-response reviewed and scored by arm before paired contrasts.
Cap-with-clear-unretracted-final is scoreable; pre-outcome truncation is missing;
normal-stop no-answer is scientific failure; repetition alone is not exclusion.
Inherited MathVision option/numeric/symbolic equivalence; all ambiguities and
deterministic20% second-pass QC. Same-agent QC is not independent reliability.
Complete A0-A3 families (all20responses resolved) form primary paired denominator.
Integer correct-count differences divided by5 avoid spurious near-zero bounds.
10000 family bootstrap draws, inherited seed120220260929; descriptive signs and
all-safe-family worst/best missingness bounds. B margins independently reconstructed
from full saved option token probabilities. Primary analysis sealed before looking
up historical majority I-/T+ selected cases. No scientific condition/label changes.

Plan thresholds unchanged: semantic>=12complete families, dummy gain>=.05 with
CI lower>0, base/shuffle gains>0; buffer>=8valid pairs, mean margin gain>0,
95%CI excludes0 and>=60%positive families. Partial means a positive primary point
estimate that fails its confirmation gate; otherwise unresolved. This convention
is frozen before outcomes, and never called robust mechanism evidence.
Target<8/hard12 allocatedGPUh; reserve whole finite job envelopes before launch.
At most460 A calls if23safe,22scientific B and12technical B requests. Up to8
available authorized GPUs via project scheduler only. Exactly one plan-matched
recommendation at completion; no follow-on experiment.
'''

LEAKAGE_NOTES={
'2963':'Only component areas/tangency/coordinates; no a,b identification or a+b.',
'2829':'Only lattice boundary/row counts; excludes speculative horizontal-edge formula, final stick formulas and answer.',
'3030':'Square/leg coordinates stop before BC length; no asked hypotenuse or its equivalent.',
'2077':'Degrees and unsolved stationarity equations; no center coin value or equation directly giving it.',
'2456':'Intercept transformation only; no selected range or truth assignment.',
'2997':'White-triangle height only; no shaded area.',
'1876':'Task-applied intersection bounds; no house/resident/Curvy binding.',
'1841':'Non-target box binding and remaining-symbol constraint; no box2 answer.',
'2213':'Symmetry fixed-point counts; no Burnside average or final painting number.',
'1124':'Coordinates/slope/intersection only; numeric1 is an incidental coordinate, not asserted area.',
'3019':'Component triangle angles only; no BAC sum or right-angle assertion.',
'825':'Fixed-placement mask intersections, no maximum, winning option or candidate answer.',
'1318':'Incidence-derived common vertex sum only; incidental6 is vertex count, not B+D.',
'603':'Erroneous column mapping proposition only; no visible-vehicle list or answer.',
'1877':'Sticker count and erroneous individual area only; no total area.',
'936':'Draft is speculative folding planning embedded in option guessing, not a stable source deduction. No safe content identified in reviewed source; exclude semantic calls, retain MC buffer.',
'353':'Erroneous observer bindings only; no resulting pole direction or option.',
'3022':'Corrected triangle relations stop before requested PQC angle or equivalent BAQ.',
'1082':'Nonwinning glyph counts only; exact maxima uncertain. No M count or winning option.',
'460':'Intermediate segment counts/distances, no sum or answer letter.',
'2742':'Stepwise neighbor counts, no product/path total.',
'2587':'Square vertices/area only; no T, PT length or solved equation determining T.',
'2890':'Coordinate bindings/rectangle height only; no fold-length evaluation.',
'392':'Vieta/divisibility/sign constraints only; no root multiset or multiplicity.'}

def main():
    from transformers import AutoTokenizer
    assert not (ROOT/'config.json').exists()
    ROOT.mkdir(parents=True,exist_ok=True)
    historical={str(p):sha(p) for base in ['outputs','reports','scripts'] for directory in sorted(Path(base).glob('stage12*'))+[Path(base)/f'stage13{x}' for x in 'abc']
        if directory.exists() for p in directory.rglob('*') if p.is_file() and not any(x in p.parts for x in ['cache','__pycache__','.pytest_cache'])}
    save(ROOT/'audit/historical_preservation.json',dict(at=now(),files=historical))
    inherited={}
    for suffix in ['frozen24_manifest','technical4_manifest','source_trace_manifest']:
        p=OLD/f'stage13c_{suffix}.json';d=load(p);inherited[suffix]=d
        save(ROOT/f'stage13d_{suffix}.json',dict(d,stage13d_inheritance=dict(at=now(),source=str(p),sha256=sha(p),rows_unchanged=True)))
    rows=inherited['frozen24_manifest']['rows'];tech=inherited['technical4_manifest']['rows']
    sources={r['item_id']:r for r in inherited['source_trace_manifest']['rows']}
    oldcfg=load('outputs/stage13a/v1/config.json');ti=AutoTokenizer.from_pretrained(oldcfg['models']['I']['model']['checkpoint']);tt=AutoTokenizer.from_pretrained(oldcfg['models']['T']['model']['checkpoint'])
    notes=copy.deepcopy(NOTES)
    notes['936']=[]
    notes['2829']=notes['2829'][:2] # Explicit speculative test, not retained as a proposition.
    notes['2890'][0]=(notes['2890'][0][0],'The fold line l is the perpendicular bisector of segment AC',notes['2890'][0][2])
    deductions=[];audits=[]
    for r in rows:
        item=r['item_id'];p=OLD/'audit/source_packets'/f'{item}.json';src=load(p);entries=[]
        assert src['base_prompt']==r['prompts']['O']
        for text,anchor,verification in notes[item]:
            pos=src['reasoning'].find(anchor);assert pos>=0,(item,anchor)
            entries.append(dict(text=text,source_quote=anchor,source_character_offset=pos,verification=verification))
        entries.sort(key=lambda e:e['source_character_offset'])
        # The compact list is content, not an unmarked quotation of the original trace.
        d='\n'.join('- '+e['text'] for e in entries)
        label='HAS_VERIFIED_ERROR' if item in ['603','1877','353'] else 'MIXED_OR_UNCLEAR' if item=='1082' else 'ALL_VERIFIED_CORRECT' if entries else 'NO_SAFE_DERIVED_CONTENT'
        deductions.append(dict(item_id=item,family_id=r['family_id'],text=d,entries=entries,n=len(ti.encode(d,add_special_tokens=False)),
            source_packet=str(p),source_packet_sha256=sha(p),source_trace_sha256=sources[item]['generation_sha256'],status='SAFE_NONEMPTY' if entries else 'NO_SAFE_DERIVED_CONTENT'))
        audits.append(dict(item_id=item,family_id=r['family_id'],SAFE_NONEMPTY=bool(entries),EXPLICIT_FINAL_PRESENT=False,ANSWER_COMMITMENT_PRESENT=False,
            GOLD_EQUIVALENT_PRESENT=False,QUESTION_RESTATEMENT_PRESENT=False,E_STAR_RESTATEMENT_PRESENT=False,
            ALL_VERIFIED_CORRECT=label=='ALL_VERIFIED_CORRECT',HAS_VERIFIED_ERROR=label=='HAS_VERIFIED_ERROR',MIXED_OR_UNCLEAR=label=='MIXED_OR_UNCLEAR',
            correctness_label=label,leakage_review=LEAKAGE_NOTES[item],first_pass='Source anchor/Q/E*/asked-target review',
            second_pass='Same-agent separate leakage/target-equivalence reread before model outputs',source_errors_corrected=False))
    save(ROOT/'stage13d_derived_state_extractions.json',dict(at=now(),status='SEALED',rows=deductions,scope='Compact extraction; not exhaustive proposition census',model_outputs_opened=False))
    save(ROOT/'stage13d_derived_state_audit.json',dict(at=now(),rows=audits,independent_raters=False,model_outputs_opened=False))
    eligible=[r for r in deductions if r['status']=='SAFE_NONEMPTY'];controls=[]
    for d in eligible:
        chosen=donor(d,eligible);n=d['n'];raw='This is additional intermediate context.'*(n+1)
        ids=ti.encode(raw,add_special_tokens=False)[:n];dummy=ti.decode(ids,skip_special_tokens=False)
        assert ti.encode(dummy,add_special_tokens=False)==ids
        controls.append(dict(item_id=d['item_id'],family_id=d['family_id'],derived=d['text'],dummy=dummy,dummy_ids=ids,derived_token_count=n,
            donor_item_id=chosen['item_id'],donor_family_id=chosen['family_id'],shuffled=chosen['text'],shuffled_token_count=chosen['n'],length_difference=abs(chosen['n']-n)))
    save(ROOT/'stage13d_semantic_context_controls.json',dict(at=now(),rows=controls,wrapper=['Intermediate deductions available so far:','Solve the original problem using the information above.']))
    initial=sorted(eligible,key=lambda r:digest('stage13c-v1|initial8|'+r['family_id']))[:8];initialids={r['item_id'] for r in initial}
    byid={r['item_id']:r for r in rows};tasks=[]
    for d in controls:
        r=byid[d['item_id']]
        for c in CONDITIONS:
            prompt=r['prompts']['O']
            if c!='I_BASE':prompt+='\n\nIntermediate deductions available so far:\n'+d[{'I_DERIVED':'derived','I_DUMMY':'dummy','I_SHUFFLED':'shuffled'}[c]]+'\n\nSolve the original problem using the information above.'
            chat=ti.apply_chat_template([dict(role='user',content=[dict(type='text',text=prompt)])],tokenize=False,add_generation_prompt=True)
            assert chat.endswith('<|im_start|>assistant\n')
            for rep in range(5):tasks.append(dict(task_id=f"A_{c}_{r['item_id']}_r{rep}",phase='semantic_initial8' if r['item_id'] in initialids else 'semantic_remaining',
                item_id=r['item_id'],family_id=r['family_id'],condition=c,model_key='I',cap=32768,seed=seed(r['family_id'],c,rep),replicate=rep,
                prompt=prompt,chat_prompt=chat,prompt_token_ids=ti.encode(chat,add_special_tokens=False),initial8=r['item_id'] in initialids))
    save(ROOT/'stage13d_semantic_seed_manifest.json',dict(at=now(),tasks=tasks,initial8_items=[r['item_id'] for r in initial],seed_rule='full SHA256 modulo2**31',generation_started=False))
    mc=[r for r in rows if r['options']];mcrows=[]
    for r in mc:
        options={chr(65+i):text for i,text in enumerate(r['options'])}
        candidate_ids={a:tt.encode(a,add_special_tokens=False) for a in options}
        assert all(len(ids)==1 for ids in candidate_ids.values()) and r['answer'] in options
        mcrows.append(dict(item_id=r['item_id'],family_id=r['family_id'],options=options,gold=r['answer'],candidate_ids=candidate_ids,representation='canonical option letter'))
    save(ROOT/'stage13d_mc_buffer_manifest.json',dict(at=now(),rows=mcrows,n=len(mcrows),minimum=8,excluded_open_ended=[r['item_id'] for r in rows if not r['options']]))
    phrase=tt.encode('Let me think.',add_special_tokens=False);close=tt.encode('</think>',add_special_tokens=False);prefix=tt.encode('Final answer:',add_special_tokens=False);assert len(close)==1
    btasks=[]
    for pool,conditions in [(tech,[('SHORT',0),('SHORT',1),('LONG',0)]),(mc,[('SHORT',0),('LONG',0)])]:
        for condition,repeat in conditions:
            for r in pool:
                n=16 if condition=='SHORT' else sources[r['item_id']]['reasoning_token_count']
                candidates={chr(65+i):tt.encode(chr(65+i),add_special_tokens=False) for i in range(len(r['options']))} if r['options'] else {'technical_gold_probe':tt.encode(r['answer'],add_special_tokens=False)}
                selected=next(iter(candidates));ids=(phrase*((n+len(phrase)-1)//len(phrase)))[:n]+close+prefix+candidates[selected]
                chat=tt.apply_chat_template([dict(role='user',content=[dict(type='text',text=r['prompts']['O'])])],tokenize=False,add_generation_prompt=True)
                assert chat.endswith('<|im_start|>assistant\n<think>\n')
                phase='technical_buffer' if pool is tech else 'scientific_buffer'
                btasks.append(dict(task_id=f"{phase}_{condition}_{r['item_id']}_r{repeat}",phase=phase,item_id=r['item_id'],family_id=r['family_id'],
                    condition='B_'+condition,model_key='T',cap=len(ids),seed=42,replicate=repeat,prompt=r['prompts']['O'],chat_prompt=chat,
                    prompt_token_ids=tt.encode(chat,add_special_tokens=False),forced_token_ids=ids,reasoning_count=n,close_id=close[0],
                    answer_prefix='Final answer:',answer_prefix_ids=prefix,candidate_ids=candidates,selected_candidate=selected,
                    technical_open_ended_probe=not bool(r['options'])))
    save(ROOT/'stage13d_buffer_forced_sequences.json',dict(at=now(),tasks=btasks,free_generated_tokens=0,reproducibility_atol=1e-5))
    paths=list(Path('scripts/stage13d').glob('*.py'))+[Path('scripts/stage13d/run.sh'),Path('scripts/stage12xs/common.py')]
    cfg=dict(at=now(),models=oldcfg['models'],runtime=oldcfg['runtime'],environment=oldcfg['environment'],
        resource=dict(target_gpu_hours=8,hard_gpu_hours=12,max_concurrent_gpus=8),source_sha256={str(p):sha(p) for p in paths},
        plan_sha256=sha('plan/stage13d_derived_state_priming_and_immediate_buffer_plan.md'))
    save(ROOT/'config.json',cfg)
    with (ROOT/'stage13d_post_evidence_mechanism_spec.md').open('x') as f:f.write(SPEC)
    frozen={str(p):sha(p) for p in ROOT.glob('*') if p.is_file()};save(ROOT/'audit/prospective_seal.json',dict(at=now(),files=frozen,scientific_outputs_opened=False,
        safe_families=len(eligible),semantic_calls=len(tasks),buffer_scientific_calls=2*len(mc),buffer_technical_calls=12,initial8_items=sorted(initialids)))
    print('A',shards('semantic_initial8',[t for t in tasks if t['initial8']],1))
    print('B_TECH',shards('technical_buffer',[t for t in btasks if t['phase']=='technical_buffer'],1))
    print('SEALED',len(eligible),'safe',len(mc),'MC',len(tasks),'A calls',len(historical),'prior files')
if __name__=='__main__':main()
