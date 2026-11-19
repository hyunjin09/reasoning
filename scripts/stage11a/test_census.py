import unittest
from scripts.stage11a.analyze_census import summarize
from scripts.stage11a.common import ARMS

class CensusTests(unittest.TestCase):
    def test_no_final_is_not_relabelled_wrong_and_unprobed_not_failure(self):
        rows=[]
        for arm in ARMS:
            rows.extend([
                dict(item_id='1',arm=arm,native='N2',probed=True,probe='PROBE_ACCESSIBLE',final='NO_VALID_FINAL',profile='P3'),
                dict(item_id='2',arm=arm,native='N5',probed=False,probe='PROBE_NOT_RUN',final='FINAL_CORRECT',profile='P5')])
        r=summarize(rows)['modes']['thinking']
        self.assertEqual(r['n'],2);self.assertEqual(r['probe_n'],1)
        self.assertEqual(r['probe_accessible']['point'],1)
        self.assertEqual(r['downstream_failure']['point'],1)
        self.assertEqual(r['downstream_wrong_only']['point'],0)
        self.assertEqual(r['downstream_no_valid_final']['point'],1)
        self.assertEqual(r['final_correct']['point'],.5)

if __name__=='__main__':unittest.main()
