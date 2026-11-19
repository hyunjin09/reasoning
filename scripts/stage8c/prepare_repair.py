"""Freeze repair cases from previous native traces, with no efficacy outcomes."""
import json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from visual_reasoning.stage8b.block0 import episodes
from scripts.stage8c.prepare import save,sha

ROOT=Path('outputs/stage8c_repair/v1')


def main():
    old=Path('outputs/stage8c_v2/v1')
    for name in ['audit/completion_seal.json','audit/technical_stop_freeze.json']:
        content=json.loads((old/name).read_text())
        for field in ('hashes','artifacts_sha256','support_sha256'):
            for p,digest in content.get(field,{}).items():assert sha(p)==digest,p
    cfg=json.loads((old/'audit/technical_config_v3.json').read_text())
    by_id={r['item_id']:r for r in cfg['technical_items']}
    index=json.loads(Path('outputs/stage8b_block0/v1/stage8b_block0_cohort_manifest.json').read_text())['rows']
    families=json.loads((old/'stage8c_v2_family_manifest.json').read_text())['item_family']
    inputs=[];cases=[]
    for rid in ['2579','2433','152','2098']:
        r=next(x for x in index if x['item_id']==rid)
        dest=Path(r['receipt']).parent
        a=np.load(dest/'passive.npz')['retrieval_score']
        onsets=[e['start_token'] for e in episodes(a,4)]
        input_row={k:by_id[rid][k] for k in ['item_id','image','image_sha256','question','generation_query']}
        assert sha(input_row['image'])==input_row['image_sha256']
        ranges=[]
        if rid in ['2579','2433']:
            ranges.append(dict(case_id=rid+'_short',length_bin='short',start=1,end=256,
                anchor=32,expected_triggered=rid=='2579',purpose='Reproduce full original failing256-token audit'))
            for lower,label in [(2048,'medium'),(8192,'long')]:
                anchor=next((t for t in onsets if t>=lower),lower) if rid=='2579' else lower
                ranges.append(dict(case_id=rid+'_'+label,length_bin=label,start=anchor,end=anchor+1,
                    anchor=anchor,expected_triggered=anchor in onsets,purpose='Frozen native onset where available; fixed boundary otherwise, without replacing families'))
        else:
            anchor=19 if rid=='152' else 32
            ranges.append(dict(case_id=rid+'_short',length_bin='short',start=anchor,end=anchor+1,
                anchor=anchor,expected_triggered=rid=='152',purpose='Independent triggered/nontriggered family'))
        for c in ranges:
            c.update(item_id=rid,family_id=families[rid],reference_R=float(a[c['anchor']]),
                     reference_is_onset=c['anchor'] in onsets)
            assert c['expected_triggered']==c['reference_is_onset']
            cases.append(c)
        inputs.append(dict(input=input_row,source_native_dir=str(dest),family_id=families[rid],cases=ranges,
            source_sha256={str(dest/n):sha(dest/n) for n in ['generation.json','passive.npz','input.json','result.json']}))
    assert len(cases)==8 and len({x['family_id'] for x in cases})>=2
    at=datetime.now(timezone.utc).isoformat()
    save(ROOT/'stage8c_repair_prefix_manifest.json',dict(at=at,cases=cases,inputs=inputs,
        scientific_outcomes_used=False,thresholds=dict(relative_l2=.02,max_abs=.125),
        replay='Original saved token IDs, native multimodal prefill, then one-token cached forwards throughout. Same positions/casts; no full-vs-cached equality requirement.'))
    cfg={k:cfg[k] for k in ['model_checkpoint','model_revision','detector_freeze','detector_freeze_sha256',
        'max_new_tokens','generation_parameters','presence_penalty','min_pixels','max_pixels']}
    cfg.update(at=at,output_dir=str(ROOT),prefix_manifest=str(ROOT/'stage8c_repair_prefix_manifest.json'),
               node='node02',gpus=2,mem='100G',cpus=8,time='01:00:00',tmux=False)
    save(ROOT/'audit/prepared_config.json',cfg)
    save(ROOT/'audit/original_scientific_freeze.json',dict(at=at,sha256={str(old/n):sha(old/n) for n in [
        'stage8c_v2_family_manifest.json','stage8c_v2_dev128_manifest.json','stage8c_v2_test512_manifest.json',
        'audit/subsets.json','audit/technical_config_v3.json','audit/completion_seal.json',
        'stage8c_v2_technical_validation.json']},
        original_gain_sha256=sha('code/visual_reasoning/stage8c/gain.py'),
        original_plan_sha256=sha('plan/stage8c_v2_retrieval_triggered_visual_gain_large_diverse_plan.md'),
        original_protocol_sha256=sha('plan/stage8c_v2_execution_protocol_v1.md')))
    print(json.dumps(dict(cases=cases,independent_families=len({x['family_id'] for x in cases})),indent=2))


if __name__=='__main__':main()
