"""Presentation-only repair; reuses immutable scientific results."""
import os
from scripts.stage10b import figures,account,report,audit
from scripts.stage10b.resource_snapshot import snapshot
from scripts.stage10b.common import ROOT,load,sha
assert os.environ.get('SLURM_JOB_ID')
assert sha(ROOT/'stage10b_yield_inference.json')==load(ROOT/'audit/presentation_revision.json')['inference_sha256']
figures.main();snapshot('presentation_running');account.main();report.main();audit.main()
