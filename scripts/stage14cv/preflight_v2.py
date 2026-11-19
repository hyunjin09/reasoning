"""Four-call operational repair validation, then finite approved R2 recovery."""
import argparse
from scripts.stage14cv.common import *
from scripts.stage14cv.operational_v2 import completed_receipt


def validate():
    out=[];files={}
    for model,condition in [('I','C1'),('T','R2')]:
        ts=[t for t in tasks('technical') if t['model_key']==model and t['condition']==condition]
        m=dict(context_ids=[t['task_id'] for t in ts]);gs=[]
        for t in ts:
            p=completed_receipt(t,m);assert p,t['task_id']
            g=load(p.parent/'generation.json');original=load(checked(t).parent/'generation.json')
            assert g['prompt_token_ids']==original['prompt_token_ids']
            assert g['sampling']==original['sampling'] and g['seed']==original['seed']
            assert g['visual_tokens']==original['visual_tokens']
            gs.append(g)
            files.update({str(q):sha(q) for q in [p,p.parent/'input.json',p.parent/'generation.json']})
        a,b=gs;prefix=a['generated_token_ids'][:128]==b['generated_token_ids'][:128]
        out.append(dict(model=model,condition=condition,prefix_exact=prefix,
                        whole_exact=a['generated_token_ids']==b['generated_token_ids'],
                        tokens=[a['tokens'],b['tokens']]))
    passed=all(r['prefix_exact'] for r in out)
    save(ROOT/'audit/operational_repair_preflight_v1.json',dict(at=now(),status='PASS' if passed else 'FAIL_HOLD',
         calls=4,comparisons=out,files=files,scientific_accuracy_inspected=False))
    assert passed,'Repair preflight failed; hold'


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--release-R',action='store_true');a=p.parse_args()
    validate()
    if a.release_R:
        from scripts.stage14cv.launch_v2 import launch
        launch('R','T','R2',3,allow_pending=True)
        save(ROOT/'audit/R2_recovery_release_v1.json',dict(at=now(),calls=66,new_primary_responses=58,
             context_only=8,C_launched=False,follow_on_launched=False))
