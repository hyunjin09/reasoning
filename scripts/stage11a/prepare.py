"""Export image/question/gold only, never model trajectories or correctness."""
import os
from pathlib import Path
from scripts.stage11a.common import ROOT, OLD, ARMS, load, save, sha, now

assert os.environ.get('SLURM_JOB_ID')
source = OLD/'stage9a_cohort_manifest.json'
rows = load(source)['rows']
assert len(rows) == len({r['family_id'] for r in rows}) == 128
packets, receipts = [], []
for r in rows:
    packet = {k:r[k] for k in ('item_id','family_id','image','image_sha256','question','options','answer','subject','level')}
    assert sha(r['image']) == r['image_sha256']
    packets.append(packet)
    files = []
    for arm in ARMS:
        d = OLD/'native/examples'/f"{arm}_{r['item_id']}"
        for name in ('generation.json','tokens.jsonl','input.json','manifest_row.json','result.json'):
            p = d/name
            assert p.is_file(), p
            files.append(p)
    receipts.append(dict(item_id=r['item_id'],family_id=r['family_id'],source_sha256={str(p):sha(p) for p in files}))
save(ROOT/'packets/evidence_construction.json',dict(at=now(),rows=packets,blinding='Only original image/question/benchmark gold; no model output or correctness labels.'))
save(ROOT/'audit/input_provenance.json',dict(at=now(),source=str(source),source_sha256=sha(source),rows=receipts,
    independent_families=128,existing_trajectories=384,model_outputs_opened=False))
print('128 blinded evidence-construction packets;384 native artifacts hashed, no native outcomes opened.',flush=True)
