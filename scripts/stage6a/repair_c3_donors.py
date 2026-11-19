"""Version only semantically invalid unrelated controls before their inference."""
import json
import hashlib
import numpy as np
from PIL import Image
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write


def load(path):return [json.loads(s) for s in path.read_text().splitlines()]


def feature(path):
    im=Image.open(path).convert('RGB');w,h=im.size;im.thumbnail((128,128))
    gray=np.asarray(im).astype(float).mean(2)/255
    return np.array([np.log(w/h),gray.mean(),gray.std(),np.abs(np.diff(gray,axis=0)).mean(),np.abs(np.diff(gray,axis=1)).mean()])


def main():
    rows=load(OUT/'cohort/c3_primary_manifest.jsonl')
    reviews={r['event_id']:r for r in load(OUT/'audit/c3_unrelated_semantic_review.jsonl')}
    intact={r['base_id']:r for r in rows if r['condition']=='intact'}
    # These full native images were explicitly inspected in the donor review.
    # Restrict replacement candidates to categories visibly absent in each image.
    ordinary={'bed','handbag','chair','knife','cell phone','cup','bicycle'}
    approved={
        'pope_94501_cup':ordinary|{'person'},
        'pope_286342_mouse':{'bottle','person','handbag','chair','knife','cell phone','bicycle'},
        'pope_495311_truck':ordinary|{'dining table','bottle'},
        'pope_205729_car':ordinary|{'dining table','bottle'},
        'pope_207205_broccoli':ordinary|{'bottle','person'},
    }
    features={k:feature(r['image_path']) for k,r in intact.items()}
    dest=OUT/'cohort/c3_primary_v2_manifest.jsonl';assert not dest.exists()
    repairs=[];audits=[];output=[]
    for row in rows:
        if row['condition']!='unrelated':output.append(row);continue
        row={**row,'source_answer':row['answer'],'answer':'no',
             'condition_ground_truth':'queried category absent in independently reviewed donor image'}
        review=reviews[row['event_id']]
        if review['review_status']!='PASS':
            candidates=[k for k,cats in approved.items() if row['category'] in cats
                and intact[k]['split']==row['split'] and intact[k]['image_id']!=row['image_id']
                and row['category'] not in intact[k]['object_inventory']]
            assert candidates,row['event_id']
            donor=min(candidates,key=lambda k:(float(np.linalg.norm(features[k]-features[row['base_id']])),k))
            original_donor=row['unrelated_donor']
            native=Image.open(intact[row['base_id']]['image_path']).convert('RGB')
            im=Image.open(intact[donor]['image_path']).convert('RGB').resize(native.size,Image.Resampling.LANCZOS)
            path=OUT/'assets/c3_unrelated_v2'/row['base_id']/'condition__unrelated.png'
            assert not path.exists();path.parent.mkdir(parents=True,exist_ok=True);im.save(path)
            row.update(image_path=str(path),unrelated_donor=donor,
                control_matching='Same fold and COCO domain; nearest aspect/brightness/contrast/edge-density among explicitly reviewed category-absent fallback images; resized to recipient dimensions.',
                donor_repair_reason=review['reason'])
            repairs.append(dict(event_id=row['event_id'],old_donor=original_donor,new_donor=donor,
                category=row['category'],reason=review['reason'],review_before_stress_inference=True,
                replacement_absence_review='Full fallback donor image inspected in review/c3_unrelated_donors.json; category absent.',
                outcome_or_internal_state_used=False))
        donor=intact[row['unrelated_donor']]
        source=Image.open(intact[row['base_id']]['image_path']).convert('RGB')
        saved=Image.open(row['image_path']).convert('RGB')
        expected=Image.open(donor['image_path']).convert('RGB').resize(source.size,Image.Resampling.LANCZOS)
        assert saved.size==source.size and saved.tobytes()==expected.tobytes()!=source.tobytes()
        assert donor['split']==row['split'] and donor['image_id']!=row['image_id']
        audits.append(dict(event_id=row['event_id'],status='PASS',donor=row['unrelated_donor'],
            saved_pixel_sha256=hashlib.sha256(saved.tobytes()).hexdigest(),source_split=row['split'],
            exact_resized_donor_pixels=True,distinct_source_image=True,queried_category_absence_reviewed=True,
            source_answer=row['source_answer'],condition_answer='no'))
        output.append(row)
    write(dest,output);write(OUT/'audit/c3_unrelated_repairs.jsonl',repairs)
    write(OUT/'audit/c3_unrelated_v2_preflight.jsonl',audits)
    print('Versioned',len(repairs),'donor replacements;',len(audits),'unrelated controls pass')


if __name__=='__main__':main()
