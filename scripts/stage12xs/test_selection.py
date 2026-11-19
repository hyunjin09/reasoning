import unittest
from scripts.stage12xs.selection import identify, components, choose

class SelectionTests(unittest.TestCase):
    def test_numeric_ids_from_other_datasets_do_not_leak(self):
        mapping={'1':'v1','2':'v2'}
        self.assertEqual(identify({'rows':[{'item_id':'1','dataset':'MathVerse'}]},mapping),set())
        self.assertEqual(identify({'rows':[{'item_id':'1','image':'/allowed/MathVision/1.jpg'}]},mapping),{'1'})
        self.assertEqual(identify({'rows':[{'item_id':'2','family_id':'v2'}]},mapping),{'2'})

    def test_exclusion_propagates_transitive_aliases(self):
        c=components(['1','2','3','4'],[['1','2'],['2','3']])
        self.assertEqual(c['1'],c['3']);self.assertNotEqual(c['1'],c['4'])

    def test_selection_is_stable_and_ignores_outcomes(self):
        rows=[dict(item_id=str(i),family_id=str(i),answer_type='open',level=1,subject='geometry',correct=i%2==0) for i in range(8)]
        a=choose(rows,3,2)
        for r in rows:r['correct']=not r['correct']
        self.assertEqual(a,choose(list(reversed(rows)),3,2))
        self.assertEqual(len(a[0]),3);self.assertEqual(len(a[1]),2)
        self.assertFalse(set(a[0])&set(a[1]))

if __name__=='__main__':unittest.main()
