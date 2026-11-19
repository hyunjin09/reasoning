"""CPU-only final scoring, independent audit and prescribed figures."""
from scripts.stage9a4.analyze import score
from scripts.stage9a4.audit import main as audit
from scripts.stage9a4.figures import main as figures

score('sink')
audit()
figures()
