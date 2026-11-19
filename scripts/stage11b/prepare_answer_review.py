"""Export output-only extraction packets only after semantic eligibility seals."""
import hashlib
from scripts.stage11b.common import ROOT,SEED,load,save,sha,now
from visual_reasoning.stage8b.v2_scoring import extract_answer

gold_path=ROOT/'annotations/discovery_evidence_final.json'
gold=load(gold_path);assert gold['sealed'] and gold['model_outcomes_opened'] is False
source={r['item_id']:r for r in load(ROOT/'stage11b_discovery_manifest_v2.json')['rows']}
tasks=load(ROOT/'discovery_tasks.json')['rows'];packets=[];keys=[]
for task in tasks:
    dest=ROOT/'discovery/results'/task['task_id'];receipt=load(dest/'result.json')
    assert not receipt['budget_interrupted']
    assert sha(dest/'generation.json')==receipt['generation_sha256']
    output=load(dest/'generation.json');text=output['raw_decoded_response'];r=source[task['item_id']]
    ident=hashlib.sha256(f"stage11b:{SEED}:extract:{task['task_id']}".encode()).hexdigest()[:20]
    packets.append(dict(packet_id=ident,text=text,options=r['options'],normal_eos=receipt['normal_eos'],
        at_length_cap=receipt['at_length_cap'],adapter_proposal=extract_answer(text,r['options'])))
    keys.append(dict(packet_id=ident,task_id=task['task_id'],item_id=task['item_id'],arm=task['arm'],generation_sha256=receipt['generation_sha256']))
packets.sort(key=lambda r:r['packet_id'])
save(ROOT/'packets/discovery_answer_review.json',dict(at=now(),rows=packets,source_eligibility_sha256=sha(gold_path),
    masking='Gold, question, image, family/arm identifiers, strata, eligibility and paired outputs omitted. Mode may be inferable from text.'))
save(ROOT/'audit/discovery_answer_key.json',dict(at=now(),rows=keys))
print('256 output-only literal-answer extraction packets; no correctness calculated')
