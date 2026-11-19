import unittest
from scripts.stage11a.protocol import probe_state, profile, localization, select_probes, feasibility

class ProtocolTests(unittest.TestCase):
    def test_partial_probe_is_not_accessible(self):
        self.assertEqual(probe_state(['CORRECT','MISSING']),'PROBE_PARTIAL')
        self.assertEqual(probe_state(['WRONG','AMBIGUOUS']),'PROBE_INACCESSIBLE')

    def test_conflicting_bottleneck_predicates_remain_mixed(self):
        label,flags=profile('PROBE_INACCESSIBLE','N2','FINAL_WRONG')
        self.assertEqual(label,'P5');self.assertEqual(flags,['P1','P3'])
        self.assertEqual(profile('PROBE_ACCESSIBLE','N5','NO_VALID_FINAL')[0],'P5')
        self.assertEqual(profile('PROBE_ACCESSIBLE','N3','NO_VALID_FINAL')[0],'P2')

    def test_availability_and_downstream_gain_overlap_is_mixed(self):
        t=dict(probe='PROBE_ACCESSIBLE',native='N2',final='FINAL_CORRECT')
        c=dict(probe='PROBE_INACCESSIBLE',native='N2',final='FINAL_WRONG')
        self.assertEqual(localization(t,c),('D',['A','C']))
        c.update(probe='PROBE_ACCESSIBLE',native='N0')
        self.assertEqual(localization(t,c),('B',['B']))

    def test_selection_invariant_to_input_order_and_unrelated_outcomes(self):
        rows=[dict(item_id=str(i),subject='a' if i<50 else 'b',evidence_type='count',correct=i%2) for i in range(80)]
        one=select_probes(rows,64)
        self.assertEqual(len(one),64)
        self.assertEqual(sum(int(x)<50 for x in one),40)
        self.assertEqual(one,select_probes(list(reversed(rows)),64))
        for x in rows:x['correct']=not x['correct']
        self.assertEqual(one,select_probes(rows,64))

    def test_go_requires_informative_independent_discordances(self):
        self.assertEqual(feasibility(64,24,7,[10,10,1],.8,.2),'NO_GO')
        self.assertEqual(feasibility(64,24,18,[10,10,1],.8,.2),'STRONG_GO')
        self.assertEqual(feasibility(40,12,9,[10,1,1],.8,.25),'LIMITED_GO')
        self.assertEqual(feasibility(64,24,18,[10,10,1],.59,.2),'NO_GO')

if __name__=='__main__':unittest.main()
