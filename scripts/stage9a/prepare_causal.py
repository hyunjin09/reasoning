"""Outcome-masked, deterministic source/readout manifest and geometry audit."""
import bisect
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from transformers import AutoTokenizer

from scripts.stage8c.prepare import save, sha
from visual_reasoning.stage3b7.roi import cell_darkness, choose_matched_irrelevant, fixed_ring

ROOT = Path('outputs/stage9a/v1')


def rectangle(box, rows, cols):
    x0,y0,x1,y1=box
    return (max(0,math.floor(y0*rows)),max(0,math.floor(x0*cols)),
            min(rows,math.ceil(y1*rows)),min(cols,math.ceil(x1*cols)))


def equal_regions(left, right, rows, cols):
    a,b=rectangle(left,rows,cols),rectangle(right,rows,cols)
    h=max(a[2]-a[0],b[2]-b[0]);w=max(a[3]-a[1],b[3]-b[1])
    result=[]
    for r,c,_,_ in (a,b):
        r=min(r,rows-h);c=min(c,cols-w)
        result.append([i*cols+j for i in range(r,r+h) for j in range(c,c+w)])
    if set(result[0])&set(result[1]):raise ValueError('overlapping donor')
    return result


def main():
    dest=ROOT/'annotations/source_review'
    inv=json.loads((dest/'inventory_reviewed.json').read_text())['images']
    candidates=json.loads((dest/'candidates.json').read_text())['rows']+json.loads((dest/'numeric_boundary_repair_candidates.json').read_text())['rows']
    decisions=[a for p in sorted(dest.glob('decisions_*.json')) for a in json.loads(p.read_text())['accepted']]
    index={r['packet_id']:r for r in json.loads((ROOT/'annotations/packet_index.json').read_text())['rows']}
    tasks={r['task_id']:r for r in json.loads((ROOT/'audit/native_tasks.json').read_text())['rows']}
    cfg=json.loads((ROOT/'stage9a_generation_config_node07.json').read_text())
    tok=AutoTokenizer.from_pretrained(cfg['models']['instruct']['checkpoint'],local_files_only=True)
    eligible=[]; exclusions=[]; cache={}
    for decision in decisions:
        if decision['candidate_index']==408:continue  # Article A, not the vertex glyph.
        row=candidates[decision['candidate_index']];pk=row['packet_id'];idx=index[pk];task=tasks[idx['task_id']]
        if pk not in cache:
            native=Path(idx['receipt']).parent
            tokens=[json.loads(l) for l in (native/'tokens.jsonl').read_text().splitlines()]
            offsets=[0]
            for t in tokens:offsets.append(offsets[-1]+len(t['decoded_token']))
            cache[pk]=(native,tokens,offsets,''.join(t['decoded_token'] for t in tokens),json.loads((native/'input.json').read_text()))
        native,tokens,offsets,text,meta=cache[pk]
        sources=inv[row['item_id']];target=next(s for s in sources if s['source_id']==decision['source_id'])
        start=row['readout_start'];end=row['readout_end']
        if decision['extend_through']:
            at=text.lower().find(decision['extend_through'].lower(),row['character_span'][1],offsets[min(start+32,len(tokens))])
            if at<0:
                exclusions.append(dict(candidate_index=row['candidate_index'],reason='binding extension not within32 local tokens'));continue
            end=bisect.bisect_left(offsets,at+len(decision['extend_through']))
        original=text[offsets[start]:offsets[end]];original_ids=[t['token_id'] for t in tokens[start:end]]
        if tok.decode(original_ids)!=original or tok.encode(original,add_special_tokens=False)!=original_ids:
            exclusions.append(dict(candidate_index=row['candidate_index'],reason='native local tokenization not reproducible'));continue
        rows,cols=meta['visual_mapping']['merged_grid_shape'][1:]
        donors=sorted((s for s in sources if s['value']!=target['value']),key=lambda s:(abs(len(s['value'])-len(target['value'])),s['source_id']))
        geometry=None
        for donor in donors:
            try:
                target_local,donor_local=equal_regions(target['box'],donor['box'],rows,cols)
                forbidden=set()
                for s in sources:
                    a,b,c,d=rectangle(s['box'],rows,cols)
                    cells=[i*cols+j for i in range(a,c) for j in range(b,d)]
                    forbidden.update(fixed_ring(cells,merged_rows=rows,merged_cols=cols,radius=1))
                image=Image.open(task['image']).convert('RGB')
                irrelevant,audit=choose_matched_irrelevant(target_local=target_local,excluded_local=sorted(forbidden),darkness_by_cell=cell_darkness(np.asarray(image),merged_rows=rows,merged_cols=cols))
                if audit['method']!='translated_target_shape_minimum_ink':continue
                geometry=(donor,target_local,donor_local,irrelevant,audit);break
            except ValueError:continue
        if geometry is None:
            exclusions.append(dict(candidate_index=row['candidate_index'],reason='no disjoint shape/cardinality-matched donor and irrelevant region'));continue
        donor,target_local,donor_local,irrelevant,audit=geometry
        a,b=row['value_offset_in_readout'];replacement=donor['value']
        if ' ' in original[a:b] and len(original[a:b].replace(' ',''))==len(replacement):
            replacement=' '.join(replacement)
        counterfactual=original[:a]+replacement+original[b:]
        cf_ids=tok.encode(counterfactual,add_special_tokens=False)
        assert original_ids!=cf_ids and tok.decode(cf_ids)==counterfactual
        visual=meta['visual_token_indices']
        eligible.append(dict(**row,source_id=target['source_id'],target_value=target['value'],donor_id=donor['source_id'],donor_value=donor['value'],
            task_id=task['task_id'],arm=task['arm'],family_id=task['family_id'],image=task['image'],image_sha256=task['image_sha256'],
            native_dir=str(native),input_sha256=sha(native/'input.json'),tokens_sha256=sha(native/'tokens.jsonl'),prompt_length=meta['prompt_token_count'],
            visual_positions=visual,merged_shape=[rows,cols],target_local=target_local,donor_local=donor_local,irrelevant_local=irrelevant,
            target_positions=[visual[i] for i in target_local],donor_positions=[visual[i] for i in donor_local],irrelevant_positions=[visual[i] for i in irrelevant],
            irrelevant_audit=audit,prefix_token_ids=[t['token_id'] for t in tokens[:start]],original_text=original,counterfactual_text=counterfactual,
            original_token_ids=original_ids,counterfactual_token_ids=cf_ids,readout_end_extended=end,seed=task['seed']))
    # Earliest eligible local claim per reviewed demand. Never rank by effects/R/accuracy.
    per_event={}
    for row in sorted(eligible,key=lambda r:(r['readout_start'],r['candidate_index'])):per_event.setdefault(row['event_id'],row)
    selected=[];counts=Counter();seen=set()
    for row in sorted(per_event.values(),key=lambda r:hashlib.sha256(r['event_id'].encode()).hexdigest()):
        key=(row['arm'],row['family_id'])
        if key in seen or counts[row['arm']]>=32:continue
        selected.append(row);seen.add(key);counts[row['arm']]+=1
    result=dict(rows=selected,counts=dict(counts),eligible_events=len(per_event),eligible_event_ids=sorted(per_event),eligible_readout_options=len(eligible),technical_exclusions=exclusions,
        selection='Earliest eligible value per semantic event, SHA256 event order, at most1 event/family/arm and32/arm',
        outcomes_used=False,frozen=False,source_files_sha256={str(p):sha(p) for p in sorted(dest.glob('*.json'))})
    save(dest/'causal_selection_reviewed.json',result)
    # Show all inventory regions for selected images; covers every possible donor.
    selected_images=sorted({r['item_id']:r['image'] for r in selected}.items(),key=lambda x:int(x[0]))
    for page in range((len(selected_images)+5)//6):
        canvas=Image.new('RGB',(1500,1080),'white');draw=ImageDraw.Draw(canvas)
        for j,(item,path) in enumerate(selected_images[page*6:(page+1)*6]):
            im=Image.open(path).convert('RGB');im.thumbnail((480,465));x=(j%3)*500+(500-im.width)//2;y=(j//3)*540+45
            canvas.paste(im,(x,y));draw.text(((j%3)*500+5,(j//3)*540+5),item,fill='black')
            for n,s in enumerate(inv[item]):
                box=[x+s['box'][0]*im.width,y+s['box'][1]*im.height,x+s['box'][2]*im.width,y+s['box'][3]*im.height]
                draw.rectangle(box,outline='red',width=1);draw.text((box[0],box[1]-12),str(n),fill='blue')
        canvas.save(dest/f'roi_reviewed_{page}.png')
    print(json.dumps({k:result[k] for k in ['counts','eligible_events','eligible_readout_options','technical_exclusions']},indent=2))


if __name__=='__main__':main()
