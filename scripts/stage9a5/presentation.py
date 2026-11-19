"""Render the qualified interpretation and figures after the control diagnostic."""
from scripts.stage9a5.infer import main as infer
from scripts.stage9a5.figures import main as figures


if __name__=='__main__':
    infer()
    figures()
