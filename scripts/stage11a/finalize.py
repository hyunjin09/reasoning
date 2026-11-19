"""Finalize the approved census after its frozen gate has resolved the optional pilot."""
import os
from scripts.stage11a.common import ROOT,load
from scripts.stage11a import account,figures,report,audit

assert os.environ.get('SLURM_JOB_ID')
decision=load(ROOT/'stage11a_go_nogo_decision.json')
assert not decision['optional_pilot_eligible'] or (ROOT/'stage11a_equal_evidence_pilot.json').exists()
account.main()
figures.main()
report.main()
audit.main()
