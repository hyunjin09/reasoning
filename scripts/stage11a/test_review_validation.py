import copy
import unittest
from scripts.stage11a.review_validation import validate_native, validate_probe


class ReviewValidationTests(unittest.TestCase):
    def test_native_rejects_invented_quote_and_duplicate_facts(self):
        p=dict(packet_id='n',reasoning_text='The circle contains four dots.',reasoning_tokens=7,facts=[dict(fact_id='f')])
        r=dict(packet_id='n',coverage_complete=True,state='N2',reason='All evidence stated.',facts=[dict(fact_id='f',status='CORRECT',reason='Explicit count.',quotes=['four dots'])])
        validate_native(r,p)
        bad=copy.deepcopy(r);bad['facts'][0]['quotes']=['five dots']
        with self.assertRaises(AssertionError):validate_native(bad,p)
        bad=copy.deepcopy(r);bad['facts']*=2
        with self.assertRaises(AssertionError):validate_native(bad,p)

    def test_probe_rejects_invalid_labels_and_empty_reasons(self):
        p=dict(packet_id='p',text='four dots',facts=[dict(fact_id='f')])
        r=dict(packet_id='p',facts=[dict(fact_id='f',label='CORRECT',reason='Explicit.',quotes=['four'])])
        validate_probe(r,p)
        bad=copy.deepcopy(r);bad['facts'][0]['label']='N2'
        with self.assertRaises(AssertionError):validate_probe(bad,p)
        bad=copy.deepcopy(r);bad['facts'][0]['reason']=''
        with self.assertRaises(AssertionError):validate_probe(bad,p)


if __name__=='__main__':unittest.main()
