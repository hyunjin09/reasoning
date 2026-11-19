import tempfile
import unittest
from pathlib import Path
from scripts.stage14cv.call_budget import reserve


class CallBudgetTest(unittest.TestCase):
    def test_retries_and_technical_calls_share_hard_total(self):
        Path('runs/stage14cv').mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir='runs/stage14cv') as d:
            p=Path(d)
            reserve(p,'R','a',0,total_limit=3,technical_limit=1)
            reserve(p,'R','a',1,total_limit=3,technical_limit=1)
            reserve(p,'technical','b',0,total_limit=3,technical_limit=1)
            with self.assertRaises(RuntimeError):reserve(p,'R','c',0,total_limit=3,technical_limit=1)

    def test_duplicate_or_excess_technical_reservations_rejected(self):
        with tempfile.TemporaryDirectory(dir='runs/stage14cv') as d:
            p=Path(d)
            reserve(p,'technical','a',0,total_limit=4,technical_limit=1)
            with self.assertRaises(RuntimeError):reserve(p,'technical','a',0,total_limit=4,technical_limit=1)
            with self.assertRaises(RuntimeError):reserve(p,'technical','b',0,total_limit=4,technical_limit=1)


if __name__=='__main__':unittest.main()
