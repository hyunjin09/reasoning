import unittest,json
from scripts.stage14d1.contracts import validate_query,parse_record,box_pixels,pixel_to_normalized,solver_suffix,safe_payload,choose_checkpoint
class ContractTests(unittest.TestCase):
 def query(self):return dict(status='QUERY',subgoal='Use the next grid entry',entity='cell',entity_id='row 3 column 4',predicate='color',spatial_reference='Rows top to bottom, columns left to right',query='What color is the cell at row 3 column 4?',answer_value=None,numeric_provenance=[dict(number='3',source='prefix',quote='row 3 column 4'),dict(number='4',source='prefix',quote='row 3 column 4')])
 def test_value_slot_rejected(self):
  q=self.query();q['answer_value']='black'
  self.assertFalse(validate_query(q,'','row 3 column 4')[0])
 def test_coordinate_numbers_need_provenance(self):
  q=self.query();self.assertTrue(validate_query(q,'','row 3 column 4')[0]);q['numeric_provenance']=[]
  self.assertFalse(validate_query(q,'','row 3 column 4')[0])
 def test_fabricated_provenance_rejected(self):
  self.assertFalse(validate_query(self.query(),'','no coordinates here')[0])
 def test_none_is_valid(self):self.assertTrue(validate_query({'status':'NONE','answer_value':None},'','')[0])
 def test_parser_does_not_use_unclosed_thinking_draft(self):
  self.assertIsNone(parse_record('{"status":"QUERY"}'))
  self.assertEqual(parse_record('draft {bad}</think>\n```json\n{"status":"NONE"}\n```'),{'status':'NONE'})
 def test_parser_rejects_trailing_text_and_duplicate_keys(self):
  self.assertIsNone(parse_record('</think>{"status":"NONE"} extra'))
  self.assertIsNone(parse_record('</think>{"status":"NONE","status":"QUERY"}'))
 def test_roi_exact_and_invalid(self):
  self.assertEqual(box_pixels([.1,.2,.6,.8],100,50),(10,10,60,40))
  self.assertEqual(pixel_to_normalized((10,10,60,40),100,50),[.1,.2,.6,.8])
  for b in [[-.1,0,1,1],[.5,.5,.5,1],[0,0,float('nan'),1]]:
   with self.assertRaises(ValueError):box_pixels(b,100,50)
 def test_oracle_fields_fail_ingress(self):
  q=dict(item_id='x',family_id='f',question='q',image='image.jpg',image_sha256='abc',prefix='p',prefix_sha256='s',seed=3,eligible=True,original_chat_prompt='u',original_messages=[],original_image_pixels=[],original_image_sizes=[])
  self.assertEqual(safe_payload(q),q)
  for key in ['gold_answer','E_star','target_subfact','native_status','human_roi']:
   with self.assertRaises(ValueError):safe_payload(dict(q,**{key:'leak'}))
 def test_resume_no_observed_value_is_not_invented(self):
  self.assertEqual(solver_suffix(None),'')
  self.assertIn('unverified',solver_suffix({'target':'AB','read_value':'3','supporting_source':'edge','uncertainty':'uncertain'}))
 def test_checkpoint_never_contains_final_or_future(self):
  text='some reasoning\n</think>Final answer: 7'; p=choose_checkpoint(text,512)
  self.assertNotIn('Final answer',p);self.assertNotIn('</think>',p)
if __name__=='__main__':unittest.main()
