"""Source-only E* reviews. Structured visual facts retain every subfield for scoring."""
from scripts.stage12xs.common import ROOT,load,save,sha,now

def record(item,facts,rationale,eligible=True):
    row=next(r for r in load(ROOT/'stage12xs_source_candidate_manifest.json')['rows'] if r['item_id']==item)
    assert sha(row['image'])==row['image_sha256']
    assert (1<=len(facts)<=4) if eligible else not facts
    save(ROOT/'annotations/primary'/f'{item}.json',dict(at=now(),item_id=item,family_id=row['family_id'],eligible=eligible,
        image_sha256=row['image_sha256'],facts=[dict(fact_id=f'E{i}',probe_request=q,gold_value=v) for i,(q,v) in enumerate(facts,1)],
        source_only_rationale=rationale,reviewer='main agent; source image and original question only',model_outcomes_used=False,
        requirements=dict(direct_image_facts=True,no_answer=True,no_downstream_derivation=True,entity_binding_preserved=True) if eligible else None))
