"""After both finite GPU jobs end: preserve terminal receipts and prepare blind review."""
import os,subprocess
from scripts.stage10c.common import ROOT,load,save,now
from scripts.stage10c.resource_snapshot import snapshot
assert os.environ.get('SLURM_JOB_ID')
snapshot('primary_terminal_automatic')
ids=load(ROOT/'stage10c_frozen_candidate_split.json')['primary_ids']
complete=[tid for tid in ids if (ROOT/'primary/cases'/tid/'result.json').exists()]
save(ROOT/'audit/primary_execution_status.json',dict(at=now(),completed=complete,expected=ids,complete=len(complete)==len(ids),scientific_analysis_started=False))
assert len(complete)==len(ids),'Incomplete GPU queue: preserve failed evidence; no automatic retries or analysis'
subprocess.run(['bash','scripts/stage10c/run.sh','scripts/stage10c/review_packet.py'],check=True)
print('PRIMARY_EXECUTION_COMPLETE; blind local review remains before scientific analysis',flush=True)
