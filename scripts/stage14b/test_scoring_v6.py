import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.stage14b.common import save, fingerprint
from scripts.stage14b import scoring_v6 as v6


class AdjudicationTests(unittest.TestCase):
    def test_falls_back_without_revision(self):
        with tempfile.TemporaryDirectory(dir='outputs/stage14b') as tmp:
            with patch.object(v6, 'ROOT', Path(tmp)), patch.object(v6, '_original', return_value={'status':'WRONG'}):
                self.assertEqual(v6.final_score('case')['status'], 'WRONG')

    def test_supersedes_but_preserves_prior(self):
        old = dict(task_id='case', status='WRONG', correct=False)
        with tempfile.TemporaryDirectory(dir='outputs/stage14b') as tmp:
            root=Path(tmp)
            record=dict(task_id='case', status='CORRECT', correct=True, supersedes_sha256=fingerprint(old))
            save(root/'scoring/score_adjudications_v6/case.json', record)
            with patch.object(v6, 'ROOT', root), patch.object(v6, '_original', return_value=old):
                self.assertEqual(v6.final_score('case'),record)
                self.assertEqual(old['status'],'WRONG')

    def test_rejects_changed_prior(self):
        with tempfile.TemporaryDirectory(dir='outputs/stage14b') as tmp:
            root=Path(tmp)
            save(root/'scoring/score_adjudications_v6/case.json',dict(supersedes_sha256='wrong'))
            with patch.object(v6, 'ROOT', root), patch.object(v6, '_original', return_value={'status':'WRONG'}):
                with self.assertRaises(AssertionError):v6.final_score('case')

if __name__=='__main__':unittest.main()
