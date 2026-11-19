from scripts.stage14d1_recovery.contracts import *
spec=load(R/'audit/analysis_code_seal.json')
assert sha(spec['script'])==spec['sha256']
from scripts.stage14d1_recovery.analyze import main
main()
