"""Only after native labels seal: export mode-blinded probe text and frozen gold."""
import os,hashlib
from scripts.stage11a.common import ROOT,load,save,sha,now
from scripts.stage11a.protocol import order

assert os.environ.get('SLURM_JOB_ID')
native=load(ROOT/'annotations/native_final.json');assert native['sealed']
manifest=load(ROOT/'stage11a_probe_manifest.json');gold={r['item_id']:r for r in load(ROOT/'audit/e_star_gold.json')['rows']}
packets=[];keys=[]
for task in manifest['rows']:
    d=ROOT/'probes/results'/task['task_id'];receipt=load(d/'result.json')
    assert receipt['generation_sha256']==sha(d/'generation.json')
    assert receipt['config_sha256']==sha(ROOT/'probe_config.json')
    g=load(d/'generation.json');rid='p_'+hashlib.sha256(('stage11a-probe:'+task['task_id']).encode()).hexdigest()[:20]
    packets.append(dict(packet_id=rid,item_id=task['item_id'],facts=gold[task['item_id']]['facts'],text=g['raw_decoded_response'],
        tokens=receipt['tokens'],normal_eos=receipt['normal_eos'],at_length_cap=receipt['at_length_cap'],
        rule='All visible probe text counts; resolve explicit retractions, persistent contradictions ambiguous. No native outcomes or mode labels.'))
    keys.append(dict(packet_id=rid,task_id=task['task_id'],item_id=task['item_id'],arm=task['arm'],receipt_path=str(d/'result.json'),receipt_sha256=sha(d/'result.json')))
save(ROOT/'packets/probe_review.json',dict(at=now(),rows=sorted(packets,key=lambda r:order(r['packet_id'])),native_sealed_sha256=sha(ROOT/'annotations/native_final.json')))
save(ROOT/'audit/probe_review_key.json',dict(at=now(),rows=keys))
print('PROBE_REVIEW_PACKETS',len(packets),'native labels already sealed')
