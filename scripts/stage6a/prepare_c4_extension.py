"""Prepare the already ordered 400-image reserve; activation is a separate gate."""
import hashlib
import json
from collections import Counter
import numpy as np
from scipy.fft import dctn
from PIL import Image
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write
from visual_reasoning.stage6a.splits import extension_assignments


def load(path):return [json.loads(s) for s in path.read_text().splitlines()]


def main():
    dest=OUT/'cohort/c4_extension_preparation';dest.mkdir(exist_ok=True)
    assert not (dest/'manifest.jsonl').exists(), 'Do not replace a prepared prospective reserve'
    reserve=[r for r in load(OUT/'c4_natural_failure/coco_native_manifest.jsonl') if r['phase']=='reserve']
    assert len(reserve)==400 and [r['random_order'] for r in reserve]==list(range(609,1009))
    existing=load(OUT/'audit/source_identity_catalog.jsonl');fresh=[]
    for row in reserve:
        im=Image.open(row['image_path']).convert('RGB');w,h=im.size
        gray=np.asarray(im.convert('L').resize((32,32),Image.Resampling.LANCZOS),dtype=float)
        low=dctn(gray,norm='ortho')[:8,:8].flatten();bits=low>np.median(low[1:]);bits[0]=False
        fresh.append(dict(base_id=row['base_id'],cohort='C4',dataset='COCO2014',phase='extension',
            width=w,height=h,source_image_id=row['image_id'],
            decoded_stimulus_sha256=hashlib.sha256(f'{w}x{h}:'.encode()+im.tobytes()).hexdigest(),
            phash=f'{sum(int(bit)<<i for i,bit in enumerate(bits)):016x}'))
    pairs=[];all_rows=existing+fresh
    for i,left in enumerate(all_rows):
        for right in all_rows[max(i+1,len(existing)):]:
            same_pixels=left['decoded_stimulus_sha256']==right['decoded_stimulus_sha256']
            aspect=abs(np.log((left['width']/left['height'])/(right['width']/right['height'])))
            distance=(int(left['phash'],16)^int(right['phash'],16)).bit_count()
            if same_pixels or (distance<=4 and aspect<=.15):
                pairs.append(dict(left=left['base_id'],right=right['base_id'],phash_distance=distance,exact_pixels=same_pixels))
    frozen_path=OUT/'cohort/prospective_source_split.json';frozen=json.loads(frozen_path.read_text())
    links=[(r['left'],r['right']) for r in pairs]
    links += [(r['left'],r['right']) for r in load(OUT/'audit/perceptual_duplicate_candidates.jsonl')]
    overlaps={r['base_id']:'historical' if r['phase']=='historical' else 'validation' for r in existing if r['phase'] in ['historical','mechanics','pilot']}
    assignments=extension_assignments(frozen['assignments'],[r['base_id'] for r in reserve],links,overlaps)
    manifest=[{**r,'phase':'extension','event_id':r['base_id']+'__intact',**assignments[r['base_id']]} for r in reserve]
    report=dict(status='PREPARED_NOT_ACTIVATED',prospective_reserve_seed=60974,images=len(manifest),
        original_split_sha256=hashlib.sha256(frozen_path.read_bytes()).hexdigest(),original_assignments_unchanged=True,
        activation_rule='After all initial 600 acquisitions and object labels, activate only if <60 confirmed hallucination bases or matched non-hallucination controls.',
        assignments=assignments,composition=dict(Counter(r['split'] for r in manifest)),
        near_or_exact_pairs=len(pairs),selection_used_outcomes_or_attention=False,
        split_exclusions_retained_in_unbiased_prevalence=True)
    write(dest/'source_identity_catalog.jsonl',fresh);write(dest/'duplicate_candidates.jsonl',pairs)
    write(dest/'manifest.jsonl',manifest);(dest/'split_preparation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='assignments'},indent=2))


if __name__=='__main__':main()
