"""Reuse only pixel/prompt-identical valid results; remeasure the three bad shams."""
import hashlib
import json
from PIL import Image
from scripts.stage6a.build_mechanics import OUT, load
from scripts.stage6a.inventory import ROOT
from scripts.stage6a.prepare_candidates import write

rows=load(OUT/'cohort/mechanics_v2_manifest.jsonl')
old_paths=list((OUT/'native/mechanics').glob('shard_*/examples/*/result.json'))
assert len(old_paths)==63,'Wait for original run completion before selecting valid reuses'
old={json.loads(p.read_text())['event_id']:p for p in old_paths}
rerun={r['event_id'] for r in rows if r['cohort']=='C1' and r['condition']=='sham_mask'}
rerun.add('mathverse_661__intact') # fourth rank validates the unchanged native baseline again
reuses=[];checks=[]
for row in rows:
    eid=row['event_id']
    if eid in rerun:continue
    path=old[eid];input_record=json.loads((path.parent/'input.json').read_text())
    expected=hashlib.sha256(Image.open(row['image_path']).convert('RGB').tobytes()).hexdigest() if not row.get('no_image') else None
    assert input_record['decoded_image_sha256']==expected,(eid,'changed image cannot be reused')
    assert input_record['prompt']==row['prompt'] and input_record['condition']==row['condition']
    checks.append(dict(event_id=eid,image_sha256=expected,prompt_exact=True,condition_exact=True))
    reuses.append(dict(event_id=eid,result_path=str(path.relative_to(ROOT)),source_run='mechanics_v1',
        reuse_basis='exact decoded pixels/prompt/condition; same frozen model/sampling/device class; no attention/effect filter'))
write(OUT/'cohort/mechanics_v2_reused_results.jsonl',reuses)
pending=[r for r in rows if r['event_id'] in rerun]
# Keep four independent ranks useful in this repair task.
pending.sort(key=lambda r:(r['condition']=='intact',r['event_id']))
write(OUT/'cohort/mechanics_v2_pending_manifest.jsonl',pending)
(OUT/'audit/mechanics_v2_reuse.json').write_text(json.dumps(dict(reused=len(reuses),remeasured=len(pending),checks=checks),indent=2)+'\n')
print(json.dumps(dict(reused=len(reuses),remeasured=len(pending))))
