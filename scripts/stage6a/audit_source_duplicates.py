"""Source identity and conservative near-stimulus candidates, without outcomes."""
import hashlib
import json
from pathlib import Path
from collections import defaultdict
import numpy as np
from scipy.fft import dctn
from PIL import Image
from scripts.stage6a.inventory import OUT, allowed
from scripts.stage6a.prepare_candidates import write
from scripts.stage6a.review_candidates import open_image


def main():
    sources=[]
    for name in ['mechanics_v2','pilot','c1_primary','c2_primary']:
        p=OUT/f'cohort/{name}_base_manifest.jsonl'
        if p.exists():sources.extend(json.loads(s) for s in p.read_text().splitlines())
    for name in ['c3_object_stress/pope_manifest.jsonl','cohort/c4_primary_manifest.jsonl']:
        sources.extend(r for r in map(json.loads,(OUT/name).read_text().splitlines()) if r['phase']=='primary')
    authored=json.loads((OUT/'config/primary_c1_authored_semantics.json').read_text())
    sources.extend({**r,'cohort':'C1','phase':'primary'} for r in map(json.loads,
        (OUT/'cohort/primary_c1_review_queue.jsonl').read_text().splitlines())
        if r['base_id'] in authored and authored[r['base_id']].get('crop_review','').startswith('pass')
        and not authored[r['base_id']].get('status','').startswith(('deferred','excluded')))
    historical={r['dataset_id'] for r in map(json.loads,(OUT/'cohort/historical_anchor_manifest.jsonl').read_text().splitlines())}
    for row in json.loads(allowed(Path('/data/dataset/MathVerse/testmini.json')).read_text()):
        if row['problem_version']=='Vision Dominant' and str(row['problem_index']) in historical:
            sources.append(dict(base_id=f"historical_mathverse_{row['problem_index']}",dataset='MathVerse',cohort='historical',phase='historical',image_path=str(allowed(Path('/data/dataset/MathVerse/images')/row['image']))))
    seen=set();records=[]
    for row in sources:
        if row['base_id'] in seen:continue
        seen.add(row['base_id']);im=open_image(row);w,h=im.size
        pixel_sha=hashlib.sha256(f'{w}x{h}:'.encode()+im.tobytes()).hexdigest()
        gray=np.asarray(im.convert('L').resize((32,32),Image.Resampling.LANCZOS),dtype=float)
        low=dctn(gray,norm='ortho')[:8,:8].flatten();threshold=np.median(low[1:])
        bits=low>threshold;bits[0]=False
        phash=sum(int(b)<<i for i,b in enumerate(bits))
        records.append(dict(base_id=row['base_id'],cohort=row['cohort'],dataset=row['dataset'],phase=row['phase'],width=w,height=h,
            decoded_stimulus_sha256=pixel_sha,phash=f'{phash:016x}',
            source_image_id=row.get('image_id',row.get('metadata',{}).get('docId',row.get('dataset_id')))))
    exact=defaultdict(list)
    for row in records:exact[row['decoded_stimulus_sha256']].append(row['base_id'])
    pairs=[]
    for i,left in enumerate(records):
        for right in records[i+1:]:
            if abs(np.log((left['width']/left['height'])/(right['width']/right['height'])))>.15:continue
            distance=(int(left['phash'],16)^int(right['phash'],16)).bit_count()
            if distance<=4:
                pairs.append(dict(left=left['base_id'],right=right['base_id'],phash_distance=distance,
                    exact_pixels=left['decoded_stimulus_sha256']==right['decoded_stimulus_sha256'],
                    status='same_pixels' if left['decoded_stimulus_sha256']==right['decoded_stimulus_sha256'] else 'candidate_requires_source_review'))
    write(OUT/'audit/source_identity_catalog.jsonl',records)
    write(OUT/'audit/perceptual_duplicate_candidates.jsonl',pairs)
    report=dict(sources=len(records),exact_duplicate_groups=[v for v in exact.values() if len(v)>1],
        perceptual_candidate_pairs=len(pairs),phash_rule='32x32 grayscale DCT low8x8, median excluding DC; Hamming<=4 and log-aspect difference<=0.15',
        interpretation='Near-image candidates require source review; no automatic semantic duplicate assertion, no generation outcome or internal state used.')
    (OUT/'audit/source_duplicate_screen.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
