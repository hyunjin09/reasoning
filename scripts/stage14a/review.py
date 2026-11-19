"""Source-review packets and strict receipt validation; never infer semantic QC."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw
from scripts.stage14a.common import ROOT, load, save, sha, now, digest

EXCLUSIONS = {
    'TEXT_SUFFICIENT': 'No task-critical image-only fact is needed.',
    'ANSWER_LEAKAGE_UNAVOIDABLE': 'A sufficient visual reading necessarily reveals the requested answer.',
    'MORE_THAN_FOUR_ATOMS': 'Minimal sufficient directly observed evidence requires more than four primary atoms.',
    'AMBIGUOUS_VISUAL_SOURCE': 'Task-critical visual content or identity cannot be stated unambiguously.',
    'MATERIAL_SOURCE_CONTRADICTION': 'Image and question are materially contradictory.',
    'UNDERSPECIFIED_SOURCE': 'Available question and image do not sufficiently specify the task.',
    'CORRUPT_SOURCE': 'Source text or image is missing/corrupt.',
}
FLAGS = ['requires_entity_binding', 'requires_quantity_reading', 'requires_spatial_relation',
         'requires_diagram_label_reading', 'requires_graph_table_reading']


def rendering(source, atoms):
    text = 'Task-critical visual evidence:\n' + '\n'.join('- ' + a for a in atoms)
    text += '\n\n' + source['question']
    if source['options']:
        text += '\n\nOptions:\n' + '\n'.join(chr(65+i) + '. ' + s for i, s in enumerate(source['options']))
    return text


def validate(source, receipt):
    assert receipt['item_id'] == source['item_id']
    assert receipt['source_image_hash'] == source['image_hash']
    assert receipt['source_question_hash'] == source['question_hash']
    assert receipt['primary_review_note'].strip()
    if receipt['decision'] == 'EXCLUDE':
        assert receipt['exclusion_reason'] in EXCLUSIONS
        assert receipt.get('final_qc_status') != 'PASS'
        return
    assert receipt['decision'] == 'ACCEPT'
    atoms, requests = receipt['e_star_atoms'], receipt['evidence_request_per_atom']
    assert 1 <= len(atoms) <= 4 and len(atoms) == len(requests)
    assert all(isinstance(x, str) and x.strip() for x in atoms + requests)
    assert len(set(atoms)) == len(atoms)
    for key in ['entity_references','units','task_critical_entities','task_critical_relations']:
        assert isinstance(receipt[key], list)
    for key in FLAGS:
        assert isinstance(receipt[key], bool)
    assert len(receipt['direct_image_grounding_rationale']) == len(atoms)
    qc = receipt['second_review']
    for field in ['eligibility', 'answer_safety', 'sufficiency', 'rendering']:
        assert qc[field] == 'PASS'
    assert qc['atoms'] == ['PASS'] * len(atoms)
    assert qc['note'].strip() and qc['same_agent'] is True
    assert receipt['final_qc_status'] == 'PASS'


def packet(start, count):
    order = load(ROOT/'stage14a_mathvision_candidate_order.json')['rows']
    by = {r['item_id']:r for r in load(ROOT/'audit/mathvision_census_source_snapshot.json')['rows']}
    selected = order[start-1:start-1+count]
    out = ROOT/'audit/packets'/f'mv_{start:04d}_{start+len(selected)-1:04d}'
    out.mkdir(parents=True, exist_ok=True)
    rows=[]
    for r in selected:
        s=by[r['item_id']]
        rows.append(dict(rank=r['rank'],**s))
    # Each full-resolution original remains separately accessible; the board is a navigation aid.
    canvas = Image.new('RGB',(1400,560*((len(rows)+1)//2)), 'white')
    d=ImageDraw.Draw(canvas)
    for j,r in enumerate(rows):
        x,y=(j%2)*700,(j//2)*560
        with Image.open(r['image']) as im:
            im=im.convert('RGB'); im.thumbnail((680,510))
            canvas.paste(im,(x+(700-im.width)//2,y+35))
        d.text((x+10,y+8),f"rank {r['rank']} | item {r['item_id']}",fill='black')
    target=out/'board.jpg'
    if not target.exists(): canvas.save(target,quality=95)
    if not (out/'source.json').exists(): save(out/'source.json',rows)
    print(json.dumps([dict(rank=r['rank'],item_id=r['item_id'],question=r['question'],options=r['options'],gold=r['gold_answer']) for r in rows],ensure_ascii=False))
    print(target)


def commit(path):
    order=load(ROOT/'stage14a_mathvision_candidate_order.json')['rows']
    by={r['item_id']:r for r in load(ROOT/'audit/mathvision_census_source_snapshot.json')['rows']}
    saved=sorted((ROOT/'audit/reviews/mathvision').glob('*.json'))
    previous=[load(p) for p in saved]
    accepted=sum(r['decision']=='ACCEPT' for r in previous)
    rows=load(path)
    for i,r in enumerate(rows,len(previous)):
        assert accepted < 1000, 'Stop immediately at 1000 final-QC accepted families.'
        expected=order[i]
        assert r['item_id']==expected['item_id'], 'Must review next frozen candidate.'
        s=by[r['item_id']]
        validate(s,r)
        accepted+=r['decision']=='ACCEPT'
        r=dict(r,rank=i+1,family_id=expected['family_id'],at=now(),
               reviewer='main agent',model_outcomes_used=False,
               original_receipt_sha256=sha(path))
        if r['decision']=='ACCEPT':
            r['equal_evidence_rendering']=rendering(s,r['e_star_atoms'])
        save(ROOT/'audit/reviews/mathvision'/f'{i+1:04d}_{r["item_id"]}.json',r)
        with (ROOT/'stage14a_e_star_eligibility_log.jsonl').open('a') as f:
            f.write(json.dumps(r,ensure_ascii=False)+'\n')
    print('SCREENED',len(previous)+len(rows),'FINAL_ACCEPTED',accepted)


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['packet','commit'])
    p.add_argument('--start',type=int);p.add_argument('--count',type=int,default=8);p.add_argument('--path')
    a=p.parse_args()
    packet(a.start,a.count) if a.action=='packet' else commit(a.path)
