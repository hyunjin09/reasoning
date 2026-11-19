import unittest
from scripts.stage14cv.analysis_core import paired_binary, transitions


class AnalysisTests(unittest.TestCase):
    def test_uncertain_outcomes_are_not_wrong(self):
        rows=[dict(family_id=str(i),x=x,y=y) for i,(x,y) in enumerate([(0,1),(1,0),(1,1),(None,0)])]
        a=paired_binary(rows,'x','y','test')
        self.assertEqual(a['paired_scored_families'],3)
        self.assertEqual(a['effect_pp'],0)
        self.assertEqual(a['planned_family_bounds_pp'],[-25,0])

    def test_all_positive_effects_and_seed_stability(self):
        rows=[dict(family_id=str(i),x=0,y=1) for i in range(8)]
        a=paired_binary(rows,'x','y','positive')
        self.assertEqual(a['ci95_pp'],[100,100])
        self.assertEqual(a,paired_binary(list(reversed(rows)),'x','y','positive'))

    def test_duplicate_independence_unit_rejected(self):
        r=dict(family_id='a',x=0,y=1)
        with self.assertRaises(ValueError):paired_binary([r,r],'x','y','bad')

    def test_four_way_transition_counts_preserve_unresolved_and_missing(self):
        r=[dict(native=a,format=b) for a,b in [('CORRECT','WRONG'),('WRONG','CORRECT'),('UNSCORABLE','CORRECT'),('CORRECT','TECHNICAL_MISSING')]]
        d=transitions(r,'native','format')
        self.assertEqual(d['CORRECT__WRONG'],1)
        self.assertEqual(d['UNSCORABLE__CORRECT'],1)
        self.assertEqual(d['CORRECT__TECHNICAL_MISSING'],1)
        self.assertEqual(sum(d.values()),4)


if __name__=='__main__':unittest.main()
