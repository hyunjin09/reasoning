"""Prospective numeric-edit candidates, appended before C1 native outcomes."""
import json
import re
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write


SPECS = {
    'MathVision': [
        (2427,'8','9','left vertical length'),(3020,'9','11','point A y-coordinate'),
        (2504,'6','8','bottom length AB'),(2512,'8','9','outer horizontal width'),
        (1146,'3','5','lower gap'),(2958,'2','4','point A x-coordinate'),
        (1735,'30','40','total horizontal extent'),(3004,'8','9','vertical height'),
        (573,'15','13','subtracted number'),(802,'30','32','rectangle width'),
        (389,'9','11','upper-left triangle area'),(355,'10','12','upper-left triangle area'),
        (393,'6','7','upper vertical length'),
    ],
    'MathVista': [
        (928,'17','19','navy blue bath mat price'),(802,'9.08','9.58','silk price'),
        (978,'9','11','Wednesday miles'),(948,'14','22','Wendy block count'),
        (245,'13','15','grilled steak price'),(801,'10','9','Thursday cartwheels'),
        (739,'10','12','baking dish price'),(312,'20','8','2003 apples quantity'),
        (268,'8','9','English muffins price'),(799,'4.00','5.00','baking dish price'),
        (517,'23','25','2014 employees'),(824,'0.06','0.08','sour apple candy price'),
        (584,'16','21','Aubrey Arts Education donation'),(471,'18','9','score eight frequency'),
        (121,'7','9','Thursday lunch price'),(323,'25','45','green gem positive effect'),
    ],
}


def main():
    path=OUT/'cohort/primary_c1_review_queue.jsonl'
    rows=[json.loads(s) for s in path.read_text().splitlines()]
    existing={r['base_id'] for r in rows}
    pool={r['base_id']:r for r in map(json.loads,(OUT/'cohort/semantic_candidate_order.jsonl').read_text().splitlines())}
    added=[]
    for dataset,specs in SPECS.items():
        for idx,value,cf,entity in specs:
            key=dataset.lower()+'_'+str(idx)
            if key in existing:continue
            source=pool[key]
            question=re.split(r'\n\s*Choices\s*:',source['question'],maxsplit=1,flags=re.I)[0]
            question=re.sub(r'<image\d+>','',question).replace('\\n','\n').strip()
            added.append({**source,'review_order':sum(r['dataset']==dataset for r in rows+added),
                'status':'pending_full_resolution_review',
                'proposed_target':dict(value=value,counterfactual=cf,entity=entity),
                'proposed_prompt':question+'\nReason carefully from the figure, then give the requested answer.',
                'selection_inputs':['source image','original question','objective editability'],
                'attention_or_causal_data_used':False,'supplement':'prospective target-size supplementation after source-identity exclusions; no C1 inference yet'})
    write(path,rows+added)
    print('Appended',len(added))


if __name__=='__main__':main()
