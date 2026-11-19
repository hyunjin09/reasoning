import unittest
from scripts.stage14b.analyze import pairs,transitions,verse_profile
from scripts.stage14b.protocol import VERSIONS

class AnalysisTests(unittest.TestCase):
    def test_native_reused_for_evidence_transitions(self):
        records=[]
        for condition,yes in [('image',False),('evidence',True)]:
            for model in 'IT':records.append(dict(identity='mv:1',family_id='f1',replicate=0,condition=condition,model=model,correct=yes,status='CORRECT' if yes else 'WRONG',version=None))
        r,table=transitions(records,'I')
        self.assertEqual(len(r),1);self.assertFalse(r[0]['native']);self.assertTrue(r[0]['equal'])
        self.assertEqual(table,{'WRONG__CORRECT':1})
    def test_mathverse_four_version_contrast_is_family_paired(self):
        records=[]
        for v in VERSIONS:
            for model in 'IT':
                yes=model=='T' and v in ('Vision Only','Vision Dominant')
                records.append(dict(identity='verse:1:'+v,family_id='vf1',replicate=0,condition='native',version=v,model=model,correct=yes,source_metadata={'clean_paired':True}))
        r=verse_profile(records)
        self.assertEqual(r['contrast_complete_families'],1);self.assertEqual(r['profile_contrast']['estimate_pp'],100)
        records[0]['correct']=None
        r=verse_profile(records)
        self.assertEqual(r['contrast_complete_families'],0)

if __name__=='__main__':unittest.main()
