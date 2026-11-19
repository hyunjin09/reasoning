import argparse,ast
from pathlib import Path
from scripts.stage10c.common import ROOT,load,save,sha,now
p=argparse.ArgumentParser();p.add_argument('--split',default='primary',choices=['primary','reserve']);args=p.parse_args()
validation=load(ROOT/'stage10c_technical_validation.json');assert validation['pass_all']
if args.split=='reserve':assert load(ROOT/'audit/primary_inference.json')['reserve_gate_pass']
split=load(ROOT/'stage10c_frozen_candidate_split.json');ids=split[args.split+'_ids']
paths=['scripts/stage10c/worker.py','scripts/stage10c/runtime.py','scripts/stage10c/access.py','scripts/stage10c/analysis.py','scripts/stage10c/protocol.py','scripts/stage10c/analyze.py','scripts/stage10c/review_packet.py']
for path in paths:ast.parse(Path(path).read_text())
save(ROOT/'audit'/f'{args.split}_manifest.json',dict(at=now(),frozen=True,ids=ids,conditions=['NATIVE','PRE_ALL_OFF','POST_ALL_OFF','POST_TARGET_OFF','POST_IRRELEVANT_OFF'],
 source_sha256={p:sha(p) for p in paths},validation_sha256=sha(ROOT/'stage10c_technical_validation.json'),config_sha256=sha(ROOT/'config.json'),
 analysis_tests_sha256=sha('runs/stage10c/v1/analysis_green.log'),all_labels_and_scoring_prospective=True))
print(args.split,len(ids),'trajectories',len(ids)*5,'logical free + NLL conditions')
