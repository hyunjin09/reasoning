"""After E* seal, expose one mode-anonymized native reasoning trace per packet."""
import os,json,hashlib,bisect
from scripts.stage11a.common import ROOT,OLD,ARMS,load,save,sha,now
from scripts.stage11a.protocol import order
from scripts.stage10b.protocol import paragraphs

assert os.environ.get('SLURM_JOB_ID')
gold=load(ROOT/'audit/e_star_gold.json');assert gold['sealed']
source={r['item_id']:r for r in load(ROOT/'packets/evidence_construction.json')['rows']}
rows=gold['rows'];ids=sorted((r['item_id'] for r in rows),key=order)
agreement=ids[:32];outside=ids[32:]
owners={i:['a','b'] if i in agreement else ['a' if outside.index(i)%2==0 else 'b'] for i in ids}
tasks=[];assignments={'a':[],'b':[]}
for g in rows:
    item=source[g['item_id']]
    for arm in ARMS:
        task=f"{arm}_{g['item_id']}";d=OLD/'native/examples'/task
        receipt=load(d/'result.json');tokens=[json.loads(s) for s in (d/'tokens.jsonl').read_text().splitlines()]
        assert sha(d/'tokens.jsonl')==receipt['provenance_sha256'][str(d/'tokens.jsonl')]
        span=receipt['reasoning_span'];selected=tokens[span['start']:span['end']]
        text=''.join(t['decoded_token'] for t in selected)
        offsets=[0]
        for t in selected:offsets.append(offsets[-1]+len(t['decoded_token']))
        parts=paragraphs(text);groups={}
        for p in parts:
            occurrence=dict(char_start=p['start'],char_end=p['end'],token_start=span['start']+bisect.bisect_right(offsets,p['start'])-1,
                token_end=span['start']+bisect.bisect_left(offsets,p['end']))
            groups.setdefault(p['text'],[]).append(occurrence)
        packet_id='n_'+hashlib.sha256(('stage11a-native:'+task).encode()).hexdigest()[:20]
        packet=ROOT/'packets/native'/f'{packet_id}.json'
        save(packet,dict(packet_id=packet_id,item_id=item['item_id'],question=item['question'],image=item['image'],facts=g['facts'],
            reasoning_text=text,reasoning_tokens=len(selected),token_character_offsets=offsets,token_offset_origin=span['start'],
            unique_paragraphs=[dict(text=s,occurrences=occ) for s,occ in groups.items()],
            boundary_certain=span['certain'],coverage='Complete native reasoning; exact repeated paragraphs grouped only for navigation. Read all unique text and inspect timing/corrections.',
            blinding='No arm, other mode, benchmark gold/final correctness or probe outputs; writing style may reveal mode.'))
        compact=packet.with_suffix('.txt')
        with compact.open('x') as f:
            f.write(f'{packet_id}\nQUESTION: {item["question"]}\nFROZEN E*: '+json.dumps(g['facts'],ensure_ascii=False)+'\n\n')
            for s,occ in groups.items():f.write('OCCURRENCES '+json.dumps(occ)+'\n'+s+'\n\n')
        for who in owners[item['item_id']]:assignments[who].append(dict(packet_id=packet_id,packet=str(packet),text=str(compact),packet_sha256=sha(packet)))
        tasks.append(dict(packet_id=packet_id,item_id=item['item_id'],family_id=item['family_id'],arm=arm,task_id=task,native_dir=str(d),
            owners=owners[item['item_id']],agreement=item['item_id'] in agreement,packet_sha256=sha(packet),reasoning_tokens=len(selected),
            total_generated_tokens=receipt['tokens'],native_receipt_sha256=sha(d/'result.json')))
save(ROOT/'audit/native_key.json',dict(at=now(),rows=tasks,agreement_item_ids=agreement,gold_sha256=sha(ROOT/'audit/e_star_gold.json')))
for who,rr in assignments.items():
    save(ROOT/'packets'/f'native_assignment_{who}.json',dict(at=now(),rows=sorted(rr,key=lambda r:order(who+r['packet_id'])),
        agreement_families=len(agreement),instruction='One packet at a time. Do not read native_key, another reviewer, mode correctness or probe output.'))
print('NATIVE_PACKETS',len(tasks),'agreement families',len(agreement),'assignments',{k:len(v) for k,v in assignments.items()})
