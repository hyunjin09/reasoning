"""Create gold-hidden response-review packets only after complete generation."""
from scripts.stage14d1_pilot.common import P,load,rows,save,sha,now


def main():
    freeze=load(P/'audit/scientific_generation_freeze_v8.json')
    assert freeze['families']==72 and freeze['logical_slots']==432
    scored=load(P/'analysis/scored_logical_rows_v8.json')['rows']
    original={r['item_id']:r for r in rows(P/'inference/families.jsonl')}
    pending={}
    for r in scored:
        if r['correct'] is None:
            pending.setdefault(r['generation_path'],[]).append(r)
    packets=[]
    for path,assignments in pending.items():
        g=load(path);r=assignments[0];raw=g['raw_decoded_response']
        closed='</think>' in raw
        body=raw.rsplit('</think>',1)[-1] if closed else None
        packet=dict(at=now(),generation_path=path,generation_sha256=sha(path),
            item_id=r['item_id'],family_id=r['family_id'],arms=[x['arm'] for x in assignments],
            original_question=original[r['item_id']]['question'],finish_reason=g['finish_reason'],
            cap_hit=g['cap_hit'],tokens=g['tokens'],think_closed=closed,final_body=body,
            raw_tail=raw[-2500:],parser_answer=r['answer'],extraction_status=r['extraction_status'],
            gold_hidden=True,review_rule='Review explicit final commitment only; do not derive an answer from unfinished reasoning. Inherited equivalence rules unchanged.')
        save(P/'annotations/response_packets_v8'/f"{g['id']}.json",packet)
        packets.append(dict(id=g['id'],item_id=r['item_id'],arms=packet['arms'],
            think_closed=closed,extraction_status=r['extraction_status'],generation_path=path))
    save(P/'annotations/response_packets_v8/index.json',dict(at=now(),physical_pending=len(packets),
        logical_pending=sum(len(x['arms']) for x in packets),packets=packets,gold_hidden=True))
    print('Gold-hidden response packets:',len(packets))

if __name__=='__main__':main()
