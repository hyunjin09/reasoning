"""Independent saved-pixel audit before primary controlled inference."""
import hashlib
import json
from collections import defaultdict
import numpy as np
from PIL import Image
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write


def load(path):return [json.loads(s) for s in path.read_text().splitlines()]


def main():
    rows=sum((load(OUT/f'cohort/{label}_manifest.jsonl') for label in ['c1_primary_v2','c2_primary','c3_primary']),[])
    identities={r['base_id']:r for r in load(OUT/'audit/source_identity_catalog.jsonl')}
    splits=json.loads((OUT/'cohort/prospective_source_split.json').read_text())['assignments']
    groups=defaultdict(list)
    for row in rows:groups[row['base_id']].append(row)
    records=[];errors=[]
    for key,conditions in groups.items():
        first=next((r for r in conditions if r['condition']=='intact'),conditions[0])
        im=Image.open(first['image_path']).convert('RGB');native=np.asarray(im);w,h=im.size
        sha=hashlib.sha256(f'{w}x{h}:'.encode()+im.tobytes()).hexdigest()
        identity_ok=sha==identities[key]['decoded_stimulus_sha256']
        if not identity_ok:errors.append([key,'intact source identity mismatch'])
        masks={name:np.asarray(Image.open(path))>0 for name,path in first.get('roi_mask_paths',{}).items()}
        if masks:
            same_area=int(masks['target'].sum())==int(masks['sham'].sum())>0
            disjoint=not bool((masks['target']&masks['sham']).any())
            if not same_area or not disjoint:errors.append([key,'target/sham area or isolation'])
        for row in conditions:
            name=row['condition'];record=dict(base_id=key,event_id=row['event_id'],condition=name,
                intact_source_identity_ok=identity_ok,source_split=splits[key]['split'])
            if row.get('no_image'):
                if row.get('image_path') is not None:errors.append([row['event_id'],'no-image asset'])
                record['no_image_manifest_valid']=row.get('image_path') is None
            elif name=='unrelated':
                donor=row['unrelated_donor'];edited=np.asarray(Image.open(row['image_path']).convert('RGB'))
                matched=edited.shape==native.shape and not np.array_equal(native,edited)
                same_fold=splits[donor]['split']==splits[key]['split']
                record.update(distinct_pixels_and_matched_dimensions=matched,donor=donor,donor_same_split=same_fold)
                if not matched or not same_fold:errors.append([row['event_id'],'unrelated identity/dimension/split'])
            elif name in ['mild','strong','mask','sham','sham_mild','sham_strong','sham_mask','counterfactual','counterfactual_render_sham']:
                edited=np.asarray(Image.open(row['image_path']).convert('RGB'))
                if edited.shape!=native.shape:errors.append([row['event_id'],'dimensions']);continue
                kind='sham' if name.startswith('sham') else 'target';mask=masks[kind]
                changed=np.any(edited!=native,axis=2)
                isolated=not bool((changed&~mask).any())
                record.update(changed_pixels=int(changed.sum()),mask_area=int(mask.sum()),outside_mask_exact=isolated,
                    matched_target_sham_area=same_area,sham_disjoint=disjoint)
                if not isolated or not changed.any():errors.append([row['event_id'],'empty or non-isolated edit'])
                if name in ['mask','sham','sham_mask']:
                    constant=bool((edited[mask]==127).all());record['opaque_mask_gray_127']=constant
                    if not constant:errors.append([row['event_id'],'nonopaque full mask'])
            records.append(record)
        print('audited',key,len(conditions),flush=True)
    write(OUT/'audit/primary_saved_pixel_checks.jsonl',records)
    report=dict(status='PASS' if not errors else 'FAIL',bases=len(groups),conditions=len(rows),errors=errors,
        checks=['intact decoded source identity','nonempty localized edits','target/sham disjoint equal area','opaque full mask','unrelated distinct pixels and dimensions','donor fold isolation','no-image manifest'],
        semantic_review=['primary_c1_authored_semantics.json','primary_c2_authored_semantics.json','c3_present_source_mask_review.jsonl','c3_absent_source_review.jsonl'],
        limitations=['C3 silhouettes, scene context and minor mask-boundary fragments can retain category clues; opaque annotated pixels do not establish zero causal information.','Related task wording is not evidence of source identity.'])
    (OUT/'audit/primary_asset_preflight.json').write_text(json.dumps(report,indent=2)+'\n')
    if errors:raise ValueError(errors)
    controlled=[]
    for row in rows:
        if row['cohort']=='C2' or row['condition']=='intact':controlled.append({**row,**splits[row['base_id']]})
    dest=OUT/'cohort/controlled_intact_manifest.jsonl'
    if dest.exists():raise FileExistsError(dest)
    write(dest,controlled)
    print(json.dumps(dict(**report,controlled_native_events=len(controlled)),indent=2))


if __name__=='__main__':main()
