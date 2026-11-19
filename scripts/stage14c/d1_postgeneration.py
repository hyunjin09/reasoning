"""Finite CPU continuation: strict raw seal, then technical-only summaries."""
from scripts.stage14c.d1_review import raw_freeze
from scripts.stage14c.technical_summary import main as summarize
if __name__=='__main__':
    raw_freeze()
    summarize()
