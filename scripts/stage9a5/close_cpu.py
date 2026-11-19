"""Post-control CPU closeout; no GPU allocation or follow-on experiment."""
from scripts.stage9a5.analyze import score
from scripts.stage9a5.infer import main as infer
from scripts.stage9a5.account import main as account
from scripts.stage9a5.audit import main as audit
from scripts.stage9a5.figures import main as figures


if __name__=='__main__':
    score('sink')
    infer()
    account()
    audit()
    figures()
