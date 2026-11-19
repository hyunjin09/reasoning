"""Finalize accounting/report/audit only; cannot submit research jobs."""
import os
from scripts.stage10ar import account,report,audit

if __name__=='__main__':
    assert os.environ.get('SLURM_JOB_ID')
    account.main()
    report.main()
    audit.main()
