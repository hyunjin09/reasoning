"""Freeze only the authorized Gate-A continuation panel after technical checks."""
from scripts.stage10a.common import ROOT,load,save,sha,now,verify_config


def main():
    verify_config();v=load(ROOT/'audit/technical_validation.json');assert v['pass_all'] and v['examples']==8
    events=load(ROOT/'stage10a_event_selection.json');byid={r['query_id']:r for r in events['rows']}
    rows=[]
    for query in events['primary_ids']:
        event=byid[query]
        for anchor in ('pre','emit','post'):
            for condition in ('text_only','image_off'):
                key=f'{query}_{condition}_{anchor}';dest=ROOT/'gate_a/results'/key
                rows.append(dict(query_id=query,image_id=event['image_id'],attribute=event['attribute'],anchor=anchor,
                    condition=condition,task_id=key,generation_path=str(dest/'generation.json'),result_path=str(dest/'result.json'),
                    prefix_tokens=event['anchors'][anchor]['native_tokens'],remaining_tokens=event['anchors'][anchor]['remaining_tokens']))
    paths=['scripts/stage10a/common.py','scripts/stage10a/runtime.py','scripts/stage10a/protocol.py','scripts/stage10a/worker.py',
           'code/visual_reasoning/stage9a3/access.py','code/visual_reasoning/stage9a_dynamics/generation.py']
    save(ROOT/'audit/gate_a_manifest.json',dict(at=now(),frozen=True,stage='gate_a',rows=rows,
        query_order=events['primary_ids'],n_images=24,logical_continuations=144,config_sha256=sha(ROOT/'config.json'),
        selection_sha256=sha(ROOT/'stage10a_event_selection.json'),validation_sha256=sha(ROOT/'audit/technical_validation.json'),
        source_sha256={p:sha(p) for p in paths}))
    print('GATE_A_MANIFEST',len(rows),flush=True)


if __name__=='__main__':main()
