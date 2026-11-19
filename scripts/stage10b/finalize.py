"""CPU-only completion; no ability to launch a follow-on experiment."""
import os
from scripts.stage10b import analyze,figures,account,report,audit
from scripts.stage10b.resource_snapshot import snapshot

if __name__=='__main__':
    assert os.environ.get('SLURM_JOB_ID')
    analyze.main();figures.main();snapshot('finalization_running');account.main();report.main();audit.main()
