"""Take the first technically resolved historical replicate, never the best answer."""
from scripts.stage13c.common import *

def main():
    from transformers import AutoTokenizer
    cfg=load(OLD/'config.json'); tok=AutoTokenizer.from_pretrained(cfg['models']['T']['model']['checkpoint'])
    close=tok.encode('</think>',add_special_tokens=False); assert len(close)==1
    rows=load(ROOT/'stage13c_frozen24_manifest.json')['rows']+load(ROOT/'stage13c_technical4_manifest.json')['rows']
    sources=[]
    for row in rows:
        checked=[]
        for rep in range(3):
            tid=f"P_T_EQ_{row['item_id']}_r{rep}"
            p=OLD/'audit/technical_adjudications'/f'{tid}.json'
            if not p.exists():p=OLD/'audit/technical_decisions'/f'{tid}.json'
            review=load(p);checked.append(dict(replicate=rep,technical_path=str(p),sha256=sha(p),valid=review['validity']['TECHNICALLY_VALID']))
            if checked[-1]['valid']:break
        else:raise RuntimeError('No technically resolved source for '+row['family_id'])
        gp=OLD/'generations'/tid/'generation.json';g=load(gp);ids=g['generated_token_ids']
        assert close[0] in ids,('Resolved source has no native close',tid)
        pos=ids.index(close[0]);rids=ids[:pos];assert pos+1<cfg['models']['T']['cap']
        sp=OLD/'audit/score_adjudications'/f'{tid}.json'
        if not sp.exists():sp=OLD/'audit/first_scores'/f'{tid}.json'
        packet=dict(at=now(),family_id=row['family_id'],item_id=row['item_id'],task_id=tid,replicate=rep,
            checked=checked,generation_path=str(gp),generation_sha256=sha(gp),source_final_correct=load(sp)['correct'],
            source_score_sha256=sha(sp),reasoning_token_count=pos,reasoning_token_ids=rids,
            reasoning=tok.decode(rids,skip_special_tokens=False),raw_response=g['raw_decoded_response'],
            question=row['question'],base_prompt=row['prompts']['O'],gold=row['answer'],facts=row['facts'])
        pp=ROOT/'audit/source_packets'/f"{row['item_id']}.json";save(pp,packet)
        sources.append({k:packet[k] for k in ['family_id','item_id','task_id','replicate','checked','generation_path','generation_sha256','source_final_correct','source_score_sha256','reasoning_token_count']})
        sources[-1].update(packet_path=str(pp),packet_sha256=sha(pp))
        print(row['item_id'],row['family_id'],'rep',rep,'L',pos,flush=True)
    save(ROOT/'stage13c_source_trace_manifest.json',dict(at=now(),rows=sources,selection_seal_sha256=sha(ROOT/'stage13c_frozen24_manifest.json'),rule='First technically resolved replicate ascending 0..2; correctness not used.'))

if __name__=='__main__':main()
