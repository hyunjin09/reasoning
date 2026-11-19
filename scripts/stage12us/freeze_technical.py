"""Freeze the two nonprimary prefix-injection checks without opening correctness."""
from pathlib import Path
from scripts.stage12us.common import ROOT,load,save,sha,now
from scripts.stage12us.protocol import canonical,seed


def main():
    old=load('outputs/stage12ts/v1/config.json')
    cfg=dict(at=now(),arms={'I':old['arms']['C'],'T':old['arms']['T']},environment=old['environment'],
             runtime=dict(old['runtime'],batch_size=18,max_images_per_prompt=0),
             seed_rule='int(SHA256(stage12us-v1|family_id|condition|replicate),16) modulo2**31; replicate=0,1,2',
             resource=dict(target_gpu_hours=5,hard_gpu_hours=7,max_concurrent_gpus=8),
             runtime_source_sha256={str(p):sha(p) for p in [Path('scripts/stage12us')/n for n in
                 ['common.py','protocol.py','worker.py','run.sh','launch.py']]})
    save(ROOT/'config.json',cfg)
    definitions=[('3011','Perhaps the answer is simply the volume of the tetrahedron',
                  'E_WRONG_OR_CONFLICTING','DERIVATION_FLAWED',
                  'Incorrect lateral correspondence AD/BE/CF versus frozen AE/BF/CD; extends P outside segment and proposes unsupported decompositions.'),
                 ('469','### Step 3: Try moving only 1 coin',
                  'E_FULL','DERIVATION_UNCLEAR',
                  'Correct 1/2/3 triangular rows and tangent hexagonal ring; no derivation of minimum moves yet.')]
    rows=[];audits=[]
    for item,marker,e,d,reason in definitions:
        p=ROOT/'audit/source_packets'/f'C_{item}.json';packet=load(p);raw=packet['raw']
        cut=raw.index(marker);prefix=canonical(raw[:cut]);dest=ROOT/'prefixes'/f'C_{item}.txt'
        dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('x') as f:f.write(prefix)
        audits.append(dict(item_id=item,source='C',raw_cut_offset=cut,cut_marker=marker,
            excluded_candidate=raw[cut:cut+240],evidence_state=e,derivation_state=d,reason=reason,
            EXPLICIT_FINAL_PRESENT=False,ANSWER_CANDIDATE_PRESENT=False,
            review_scope='Entire retained prefix reviewed; no target output or correctness used.',
            prefix_path=str(dest),prefix_sha256=sha(dest),source_packet_sha256=sha(p)))
        for target in ['I','T']:
            condition='TECH_RC_'+target
            for replicate in range(3):
                rows.append(dict(task_id=f'{condition}_{item}_r{replicate}',phase='technical',cohort='technical',
                    item_id=item,family_id=packet['family_id'],question=packet['question'],target=target,
                    source='C',condition=condition,replicate=replicate,seed=seed(packet['family_id'],condition,replicate),
                    prefix_path=str(dest),prefix_sha256=sha(dest)))
    save(ROOT/'audit/technical_prefix_audit.json',dict(at=now(),rows=audits,correctness_not_inspected=True,
        cut_rule='Before first explicit task-answer candidate, including conjectures/trials; intermediate quantities and unresolved generic formulas are not final task answers.'))
    save(ROOT/'audit/technical_execution.json',dict(at=now(),tasks=rows,config_sha256=sha(ROOT/'config.json'),
        require='All12 calls: exact original question/prefix, zero image tokens, continuation after prefix, both targets, no source answer, scoreable outcome. No correctness gate.'))
    for target in ['I','T']:
        save(ROOT/'queues'/f'technical_{target}.json',dict(frozen=True,phase='technical',target=target,
            config_sha256=sha(ROOT/'config.json'),rows=[r for r in rows if r['target']==target]))
    print('Frozen12 technical calls; prefix lengths',[(a['item_id'],a['raw_cut_offset']) for a in audits])


if __name__=='__main__':main()
