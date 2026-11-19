"""Direct image-reviewed pilot semantics; authored before pilot inference."""
import json
from scripts.stage6a.inventory import OUT

c1=[
 ['mathverse_712',[175,158,189,179],[260,140,277,164],'8','9','pyramid vertical height','288.68','305.91'],
 ['mathverse_721',[251,119,278,143],[280,160,307,184],'12','14','prism height','12*x^2+144*x+384','14*x^2+168*x+448'],
 ['mathvision_2516',[429,109,474,153],[440,180,485,224],'22','32','rectangle height decimal digits','0.088','0.128'],
 ['mathvision_1031',[15,43,38,79],[100,160,123,196],'3','4','outer-square upper-left offset','34','41'],
 ['mathvista_375',[177,161,205,210],[350,238,378,287],'1','2','constant on side AC','7','12'],
 ['mathvista_855',[239,135,273,174],[266,195,300,234],'11','23','left angle additive constant','14','13']]
overrides={
 'mathverse_712':dict(answer_audit='Independent geometry: square base10mm, vertical height8mm; total surface100+20sqrt89=288.6796mm². Dataset answer288.6m² has rounding/unit errors, preserved separately.',other_sources=[dict(source_id='X',roi=[159,299,212,326],entity='square base side',value='10')]),
 'mathverse_721':dict(other_sources=[dict(source_id='X',roi=[169,1,232,28],entity='first base side',value='x+4'),dict(source_id='Y',roi=[246,49,316,75],entity='second base side',value='x+8')]),
 'mathvision_2516':dict(prompt='Find the area of the rectangular region in square metres. Reason carefully, then give the numerical value.',answer_format_normalization='Original multiple-choice area stem rewritten as the same free-form area question; original answerA corresponds to0.088m².',ground_truth_readouts={'intact':'0.22','counterfactual':'0.32'},other_sources=[dict(source_id='X',roi=[174,240,230,281],entity='rectangle width',value='0.4')]),
 'mathvision_1031':dict(other_sources=[dict(source_id='X',roi=[266,65,289,104],entity='outer-square upper-right offset',value='5')]),
 'mathvista_375':dict(prompt='Find the length of AC in the isosceles triangle ABC. Reason carefully, then give the numerical length.',answer_format_normalization='Preserve question and numerical ground truth; omit fixed choices to permit semantic counterfactual values.',other_sources=[dict(source_id='X',roi=[488,164,637,211],entity='side BC expression',value='5*x-0.5')]),
 'mathvista_855':dict(prompt='Find x so that lines a and b are parallel. Reason carefully, then give the numerical value of x.',answer_format_normalization='Preserve parallel-line question and numerical ground truth; omit fixed choices.',other_sources=[dict(source_id='X',roi=[317,137,419,174],entity='right angle expression',value='8*x+1')])}
c2=[
 dict(base_id='docvqa_32152',roi=[1088,1828,1270,1879],other_roi=[1088,1760,1270,1810],entity='Documentation',other_entity='Meeting Room Rentals',answers=['3500.00','1500.00'],prompts=[
  'What amount is budgeted for Documentation?',
  'In the budget that includes Documentation, what amount is listed for Meeting Room Rentals?',
  'What amount appears in the second-to-last row of the budget table?',
  'What amount appears in the third-to-last row of the budget table?']),
 dict(base_id='docvqa_64306',roi=[1338,412,1390,449],other_roi=[1338,464,1390,501],entity='Appendix B',other_entity='Appendix C',answers=['40','43'],prompts=[
  'On what page does Appendix B begin?',
  'In the contents list containing Appendix B, on what page does Appendix C begin?',
  'What page number ends the second appendix entry in the contents list?',
  'What page number ends the third appendix entry in the contents list?']),
 dict(base_id='docvqa_50274',roi=[602,515,698,551],other_roi=[343,477,417,513],entity='ZIP code',other_entity='street number',answers=['20418','2101'],prompts=[
  'What ZIP code is printed in the address on this postcard?',
  'For the address with the ZIP code, what street number is listed on Constitution Avenue?',
  'Which five-digit number ends the last address line?',
  'Which four-digit number begins the second-to-last address line?']),
 dict(base_id='docvqa_54312',roi=[472,1380,613,1422],other_roi=[470,1452,565,1498],entity='Invoice',other_entity='Date',answers=['068-0101','3/9/98'],prompts=[
  'What invoice number appears in the billing block?',
  'In the billing block containing the invoice number, what date is listed?',
  'Which identifier starts with a hash symbol in the three-row billing block?',
  'What slash-separated value appears in the middle row of the three-row billing block?']),
 dict(base_id='docvqa_6403',roi=[1468,533,1560,570],other_roi=[1468,695,1560,741],entity='Sku Available',other_entity='Sku on Hand',answers=['3888','4746'],prompts=[
  'What quantity is listed as Sku Available?',
  'In the stock listing containing Sku Available, what quantity is listed as Sku on Hand?',
  "What four-digit quantity appears on the line immediately below 'Sku Reserved'?",
  "What four-digit quantity appears on the line immediately above 'Future Net Rsvd'?" ]),
 dict(base_id='docvqa_8048',roi=[588,507,707,546],other_roi=[588,578,707,618],entity='Promotion #',other_entity='Item #',answers=['803048','555965'],prompts=[
  'What is the Promotion # on this form?',
  'On the form containing Promotion #, what is the Item #?',
  'What six-digit identifier begins the line immediately above the item field?',
  'What six-digit identifier begins the line immediately above the SKU Quantity field?'])]
path=OUT/'config/pilot_semantic_definitions.json'
if path.exists():raise FileExistsError(path)
path.write_text(json.dumps(dict(c1=c1,c1_overrides=overrides,c2=c2),indent=2)+'\n')
print(path)
