import unittest
from scripts.stage14c.source_finalize import merge_reviews, answer_kind

class FinalizeTests(unittest.TestCase):
    def setUp(self):
        self.p = dict(review_rank=0, family_id='f', label='ELIGIBLE', evidence_atoms=[{'text':'old'}])
    def test_confirm_cannot_undo_correction(self):
        second = dict(self.p, decision='CORRECT', evidence_atoms=[{'text':'new'}])
        stale = dict(self.p, decision='CONFIRM')
        with self.assertRaisesRegex(ValueError, 'stale'):
            merge_reviews([self.p], [('second',second), ('reread',stale)])
    def test_explicit_correction_and_family_join(self):
        correction = dict(self.p, decision='CORRECT', label='UNDERSPECIFIED', evidence_atoms=[])
        final,_ = merge_reviews([self.p],[('second',correction)])
        self.assertEqual(final[0]['label'],'UNDERSPECIFIED')
        with self.assertRaisesRegex(ValueError,'family'):
            merge_reviews([self.p],[('second',dict(correction,family_id='other'))])
    def test_missing_label_blind_confirmation(self):
        second = dict(self.p,decision='CONFIRM_ELIGIBLE');second.pop('label')
        final,h = merge_reviews([self.p],[('second',second)])
        self.assertEqual(final[0]['label'],'ELIGIBLE');self.assertEqual(len(h[0]),2)
    def test_unknown_schema_stops(self):
        with self.assertRaises(ValueError):answer_kind({'benchmark':'BlindTest','category':'new task'})
        self.assertEqual(answer_kind({'benchmark':'BlindTest','category':'Subway Connections'}),'integer')

if __name__=='__main__':unittest.main()
