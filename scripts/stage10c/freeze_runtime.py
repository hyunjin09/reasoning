from pathlib import Path
import ast
from scripts.stage10c.common import ROOT,load,save,sha,now,SEED
paths=['scripts/stage10c/runtime.py','scripts/stage10c/access.py','scripts/stage10c/protocol.py','scripts/stage10c/validate.py',
 'code/visual_reasoning/stage9a3/access.py','code/visual_reasoning/stage3c9/streaming.py','code/visual_reasoning/stage8b/v2_protocol.py']
for p in paths:ast.parse(Path(p).read_text())
old=load('outputs/stage9a/v1/stage9a_generation_config.json')
save(ROOT/'config.json',dict(at=now(),model=old['models']['thinking'],source_sha256={p:sha(p) for p in paths},
 seed=SEED,free_generation='greedy',dtype='bfloat16',tf32=False,language_layers=list(range(28)),
 window_tokens=24,local_scoring_tokens=64,prefix_chunk=64,max_generated_local=88,
 frozen_artifact_sha256={str(ROOT/p):sha(ROOT/p) for p in ['stage10c_frozen_candidate_split.json','stage10c_b_gold_annotations.json','stage10c_roi_controls.json','stage10c_causal_reopening_spec.md']},
 optional_construction_sha256=sha(ROOT/'audit/demand_swap_constructions.json'),hard_total_gpu_hours=4))
print('Runtime configuration frozen; no interventions executed')
