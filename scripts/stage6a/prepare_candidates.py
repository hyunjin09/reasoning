"""Prospective semantic-only candidate order; images remain in read-only sources."""
from pathlib import Path
import json
import random
import re
import pyarrow as pa
from scripts.stage6a.inventory import ROOT, OUT, allowed


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rows))


def read_arrow(path):
    with pa.memory_map(str(allowed(path)), 'r') as source:
        return pa.ipc.open_stream(source).read_all()


def append_table_candidates(candidates,datasets):
    """Reproduce the pre-inference TabMWP supplement without reshuffling geometry."""
    existing={r['base_id'] for r in candidates};pool=[]
    for shard in datasets['MathVista']['candidates'][0]['arrow_shards']:
        table=read_arrow(shard['path']).drop(['decoded_image'])
        for i,row in enumerate(table.to_pylist()):
            key='mathvista_'+str(row['pid'])
            if row['metadata']['source']!='TabMWP' or key in existing:continue
            pool.append(dict(base_id=key,dataset='MathVista',dataset_id=str(row['pid']),
                arrow_path=shard['path'],arrow_row=i,image_column='decoded_image',
                question=row['question'],prompt=row['question'],answer=row['answer'],options=row.get('choices'),
                metadata=row['metadata'],review_stratum='localized_table_value'))
    random.Random(60971).shuffle(pool)
    for row in pool:row['prospective_order']=len(candidates);candidates.append(row)
    return candidates


def main():
    assert not (OUT/'cohort/semantic_candidate_order.jsonl').exists(), 'Preserve frozen prospective order'
    inventory=json.loads((OUT/'cohort/dataset_inventory.json').read_text())
    datasets={r['dataset']:r for r in inventory['datasets']}
    assert all(datasets[d]['usable'] for d in ('MathVerse','MathVision','MathVista','DocVQA','POPE','COCO2014'))
    historical=set()
    # All previous selected MathVerse bases remain historical regardless of outcome.
    for stage in ('stage3c9r','stage3c10','stage4a','stage5a'):
        for p in (ROOT/'outputs'/stage/'cohort').glob('*.jsonl'):
            if any(x in p.name for x in ('manifest','events','atlas')):
                for line in p.read_text().splitlines():
                    r=json.loads(line)
                    if r.get('base_problem_id') is not None and 'screen' not in p.name:
                        historical.add(str(r['base_problem_id']))
    prior_path=ROOT/'outputs/stage5a/config/cohort_rules.json'
    prior=json.loads(prior_path.read_text())
    # Prior exclusions are recorded explicitly below; no historical effects read.
    for key,value in prior.items():
        if key=='prior_excluded_bases' and isinstance(value,list):
            historical.update(str(v) for v in value if isinstance(v,(str,int)) and str(v).isdigit())
    rows=json.loads(Path('/data/dataset/MathVerse/testmini.json').read_text())
    mv=[]
    for r in rows:
        if r['problem_version']!='Vision Dominant' or str(r['problem_index']) in historical:
            continue
        mv.append(dict(base_id='mathverse_'+str(r['problem_index']),dataset='MathVerse',
            dataset_id=str(r['problem_index']), sample_id=str(r['sample_index']),
            image_path=str(allowed(Path('/data/dataset/MathVerse/images')/r['image'])),
            question=r['question'],prompt=r['query_cot'],answer=r['answer'],metadata=r['metadata']))
    candidates=[]
    for name,pool in [('MathVerse',mv)]:
        random.Random(60971).shuffle(pool);candidates.extend(pool)
    for name in ('MathVision','MathVista','DocVQA'):
        pool=[]
        for shard in datasets[name]['candidates'][0]['arrow_shards']:
            path=shard['path'];table=read_arrow(path)
            column='image' if name=='DocVQA' else 'decoded_image'
            plain=table.drop([column]).to_pylist()
            for i,r in enumerate(plain):
                if name=='MathVision':
                    eligible=r['subject'] in ('geometry','plane_geometry','solid_geometry') or bool(re.search(r'triangle|circle|angle|radius|rectangle|area|perimeter',r['question'],re.I))
                    idx=str(r['id']);answer=r['answer'];meta={'subject':r['subject'],'level':r['level']}
                elif name=='MathVista':
                    meta=r['metadata'];eligible=bool(re.search(r'geometry|geoqa|geometry3k',json.dumps(meta),re.I));idx=str(r['pid']);answer=r['answer']
                else:
                    eligible=bool(r['answers']);idx=str(r['questionId']);answer=r['answers'];meta={'docId':r['docId']}
                if not eligible:continue
                pool.append(dict(base_id=name.lower()+'_'+idx,dataset=name,dataset_id=idx,
                    arrow_path=path,arrow_row=i,image_column=column,question=r['question'],
                    prompt=r['question'],answer=answer,options=r.get('options',r.get('choices')),metadata=meta))
        random.Random(60971).shuffle(pool)
        # DocVQA candidates are grouped by document image identity before authoring.
        if name=='DocVQA':
            seen=set();unique=[]
            for r in pool:
                key=r['metadata']['docId']
                if key not in seen:seen.add(key);unique.append(r)
            pool=unique
        candidates.extend(pool)
    for i,r in enumerate(candidates):r['prospective_order']=i
    candidates=append_table_candidates(candidates,datasets)
    write(OUT/'cohort/semantic_candidate_order.jsonl',candidates)
    write(OUT/'cohort/historical_anchor_manifest.jsonl',[dict(dataset='MathVerse',dataset_id=b,role='historical_exclusion',fresh_confirmation=False) for b in sorted(historical,key=lambda x:int(x) if x.isdigit() else 10**9)])
    coco=json.loads(Path('/data/dataset/COCO2014/annotations/instances_val2014.json').read_text())
    images=sorted(coco['images'],key=lambda r:r['id']);random.Random(60974).shuffle(images)
    c4=[dict(base_id=f"coco2014_{r['id']}",dataset='COCO2014',image_id=r['id'],image_path=str(Path('/data/dataset/COCO2014/val2014')/r['file_name']),width=r['width'],height=r['height'],license_id=r['license'],random_order=i,
        phase='mechanics' if i<3 else 'pilot' if i<9 else 'primary' if i<609 else 'reserve',
        cohort='C4',condition='intact',prompt='Describe the visible objects and their arrangement in this image accurately. Reason carefully from what is visible, and then give a concise description. Avoid adding details that are not supported by the image.') for i,r in enumerate(images[:1009])]
    write(OUT/'c4_natural_failure/coco_native_manifest.jsonl',c4)
    print(json.dumps(dict(candidates={name:sum(r['dataset']==name for r in candidates) for name in ('MathVerse','MathVision','MathVista','DocVQA')},historical_mathverse=len(historical),c4=len(c4)),indent=2))


if __name__=='__main__':main()
