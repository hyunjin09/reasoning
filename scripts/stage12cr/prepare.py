"""Prospective branch freeze; no correctness or generated outputs used in selection."""
import copy,hashlib,shutil
from pathlib import Path
from scripts.stage12cr.common import ROOT,OLD,load,save,sha,now
from scripts.stage12cr.protocol import select_fresh,authorize_manifest

def main():
    assert not ROOT.exists()
    ROOT.mkdir(parents=True);(ROOT/'audit').mkdir()
    plan=Path('plan/stage12cr_decoupled_cot_science_thinking_completion_validation_plan.md')
    shutil.copyfile(plan,ROOT/'audit/approved_plan.md')
    shutil.copyfile('reports/index.md',ROOT/'audit/report_index_before_launch.md')
    preserved=load(OLD/'audit/preserved_history_hashes.json')['files']
    for p,h in preserved.items():assert sha(p)==h,p
    for folder in [OLD,Path('reports/stage12c/v1'),Path('scripts/stage12c')]:
        for p in folder.rglob('*'):
            if p.is_file() and '__pycache__' not in str(p):preserved[str(p)]=sha(p)
    save(ROOT/'audit/preserved_history_hashes.json',dict(at=now(),files=preserved))
    old=load(OLD/'stage12c_frozen_bottleneck_manifest.json');cfg=copy.deepcopy(load(OLD/'config.json'))
    cfg.update(at=now(),parent_config_sha256=sha(OLD/'config.json'))
    cfg['arms']['T']['cap']=81920
    cfg['resource']={'cot_hard_gpu_hours':5,'same12_hard_gpu_hours':2.5,'fresh12_hard_gpu_hours':2.5,'max_concurrent_gpus':8}
    sources=[Path('scripts/stage12cr')/x for x in ['common.py','protocol.py','worker.py','run.sh','launch.py','resources.py','prepare.py']]
    cfg['source_sha256'].update({str(p):sha(p) for p in sources})
    save(ROOT/'config.json',cfg)
    fresh=select_fresh(old['rows'],old['sanity_ids'])
    tasks=[t for t in old['tasks'] if t['arm']=='C' and t['item_id'] in old['remaining_ids']]
    tasks += [dict(t,cap=81920) for t in old['tasks'] if t['arm']=='T' and t['item_id'] in old['sanity_ids']+fresh]
    execution=dict(at=now(),frozen=True,config_sha256=sha(ROOT/'config.json'),tasks=tasks,
        cot_ids=old['remaining_ids'],same12_ids=old['sanity_ids'],fresh12_ids=fresh)
    save(ROOT/'audit/execution_manifest.json',execution)
    cot=dict(at=now(),frozen=True,tasks=[t for t in old['tasks'] if t['arm']=='C'],reuse_ids=old['sanity_ids'],new_ids=old['remaining_ids'],
        frozen_parent_sha256=sha(OLD/'stage12c_frozen_bottleneck_manifest.json'),config_sha256=sha(ROOT/'config.json'),
        reuse_origin=str(OLD),rows=old['rows'],labels=old['labels'],n_facts=157)
    save(ROOT/'stage12cr_cot_manifest.json',cot)
    for rank in range(3):
        ids=old['remaining_ids'][rank::3]
        m=dict(frozen=True,phase='cot',arm='C',config_sha256=sha(ROOT/'config.json'),rows=[t for t in tasks if t['arm']=='C' and t['item_id'] in ids])
        authorize_manifest(m,execution);save(ROOT/f'audit/cot_{rank}.json',m)
    for phase,ids in [('same12',old['sanity_ids']),('fresh12',fresh)]:
        m=dict(at=now(),frozen=True,phase=phase,arm='T',config_sha256=sha(ROOT/'config.json'),
            selection='Original sealed12' if phase=='same12' else 'SHA256(stage12tr-fresh-validation-v1|family_id), 5MC/7open, identity+answer type only, original12 excluded',
            rows=[t for t in tasks if t['arm']=='T' and t['item_id'] in ids])
        authorize_manifest(m,execution,True);save(ROOT/f'stage12tr_{phase}_manifest.json',m)
    rules=copy.deepcopy(load(OLD/'audit/analysis_rules.json'))
    rules.update(at=now(),decision='CoT informative if >=5 B1 or >=5 B4 rescues; technical breakdown only input/scoreability; no Thinking scientific analyses.',
        full_gate=dict(input_valid=61,scoreable_minimum=51,pre_outcome_caps_maximum=5),
        full_gate_rationale='Preserve the Stage12C prospective full61 gate (51 scoreable/5 pre-outcome caps) to operationalize substantially worse, without tuning to new outcomes.',
        stopping='Branch A five figures/exactly one scientific recommendation; Branch B technical decision only, no rerun or third cap.',
        random_audit=dict(seed='stage12c-audit-v1',family_hash_order=rules['random_audit']['family_hash_order'],rule='C-only: every ambiguity plus ceil20% unambiguous families in inherited deterministic order.'),
        trace_evidence=dict(rules['trace_evidence'],arms=['C']))
    save(ROOT/'audit/analysis_rules.json',rules)
    (ROOT/'stage12cr_cot_scientific_spec.md').write_text(f'''# Stage12C-R CoT scientific specification\n\nFrozen {now()}, before any new generation or CoT correctness inspection. Approved plan retained in audit/approved_plan.md. Preserve all61families/157facts, sealed E/N/O labels and all prior artifacts. Reuse12 C outputs unchanged, generate49 once across3 finite one-GPU batches(17/16/16); BF16/vLLM0.11.0, batch limit18, max model length128000, exact inherited image/prompt/seed. C checkpoint ebb281ec70b05090aa6165b016eac8ec08e71b17; suffix ` Let's think step by step.`; temperature.7/top-p.8/top-k20/repetition1/presence1.5/cap32768.\n\nPathology-aware validity and inherited prospective full gate61valid/51scoreable/<=5pre-outcome caps retained; repetition is data. Seal input checks and technical labels for all61 before C-only correctness packets. Annotate26 trace packets against frozen facts before correctness; no E/N/O/Blabels in scoring/trace packets. First/ambiguity-triggered and deterministic20% second scoring, same frozen MathVision equivalence. Same-agent separate-pass review is not independent reliability.\n\nA-P1/B1 and A-P2/B4 rescue proportions use scoreable C denominators; report frozen11, missingness, observed k/11 and bounds separately. A-P3 difference:4000 stratified family bootstrap seed{cfg['bootstrap_seed']}, equal weight. Wilson95% intervals. Paired N→C jointly scoreable only; missing never wrong. B2/B3 and B1 subtypes descriptive. TRACE_E_NOT_EXTERNALIZED does not mean hidden evidence absent.\n\nInformative iff B1 or B4 has>=5 rescues; otherwise sparse. Exactly one plan-prescribed recommendation, not executed. Five figures required. Target<3.5/hard5GPUh, finite60-minute requests on3 GPUs, automatic release. Branch B never gates CoT.\n''')
    (ROOT/'stage12tr_completion_spec.md').write_text(f'''# Stage12T-R cap-only completion validation\n\nFrozen {now()}, before generation. Exactly old T input/checkpoint1de27d8c51f12e819435303b9e84c4e25ba8401e, original question/no CoT, image/preprocessing/BF16vLLM/runtime/seed. Only max_tokens40960→81920;temperature1/top-p.95/top-k20/repetition1/presence0. Same12 uses original task ordering and one GPU; compare generated token prefixes diagnostically. No correctness or rescue analysis.\n\nFresh12 already frozen using SHA256(stage12tr-fresh-validation-v1|family_id), first5MC/7open eligible ranks after excluding original12; selected IDs{fresh}. Same12 gate12valid/>=11scoreable/<=1pre-outcome caps, no repetition threshold. Fresh12 only if CAP_EXTENSION_PROMISING; gate12valid/>=10scoreable/<=1pre-outcome caps. Any input invalidity prevents passage. Each phase target<1.5/hard2.5GPUh; one finite150-minute GPU allocation each, phase2 conditional. No third cap, decoding search or full T science. Prefix divergence limits paired attribution but is not a gate. If validated, prepare future Stage12T-S plan but do not execute it.\n''')
    freeze=[ROOT/'config.json',ROOT/'stage12cr_cot_manifest.json',ROOT/'stage12cr_cot_scientific_spec.md',ROOT/'stage12tr_completion_spec.md']+list((ROOT/'audit').glob('*.json'))+list(ROOT.glob('stage12tr_*manifest.json'))
    save(ROOT/'audit/prospective_freeze.json',dict(at=now(),new_generation_started=False,cot_correctness_opened=False,thinking_correctness_prohibited=True,files={str(p):sha(p) for p in freeze}))
    print('Frozen',len(tasks),'possible new calls;49C+12sameT+conditional12freshT;fresh',fresh,'historical files',len(preserved))

if __name__=='__main__':main()
