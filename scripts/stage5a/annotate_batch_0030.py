"""Human score-blind review for screen positions30–39."""
from scripts.stage5a.annotate_batch_0010 import fact,event,record
from scripts.stage5a.prepare import OUT,write_json
rows=[
record(61,'parallel_isosceles_triangle',{'A':fact('angle CDE','74','84',[68,40,116,71])},[
event('A','angle at D is given as 74°, which is angle CDE','74'),event('A','Given angle CDE = 74°, so angle CED','74')]),
record(62,'parallel_extended_transversal',{'A':fact('angle BAE','40','50',[175,53,219,83])},[
event('A',"There's an angle of 40 degrees at point A between AB and AE",'40'),event('A','so angle EAB = 40°, so angle BAC','40',use_last=True)]),
record(63,'similar_triangles_shadow',{'A':fact('bracket AB','3','4',[72,236,95,264]),'B':fact('bracket AC','9','8',[141,249,164,281]),'C':fact('vertical BE','2','3',[124,187,151,216])},[
event('A','AD is 3 units','AD','AB',readout_kind='entity_binding'),event('B','DC is 9 units','DC','AC',readout_kind='entity_binding',correctness='UNDECIDABLE',claim_note='Native immediately questions this reading; preserve uncertainty.'),event('A','then the shadow length is AD = 3','AD','AB',readout_kind='entity_binding',use_last=True)], 'Image marks AB3, AC9, BE2. Native repeatedly names the footB asD and misbinds totalAC9 as partDC9, leading to an incorrect additivebase12.',evidence_type='length_label'),
record(65,'parallel_two_transversals',{'A':fact('angle4','30','40',[132,111,178,140])},[
event('A','with a 30° angle between angle 4 and line b','30',correctness='UNDECIDABLE',claim_note='Number exists but the first relational description does not specify the angle4 binding clearly.'),event('A','Given angle 4 = 30° (from the diagram)','30')]),
record(66,'parallel_zigzag',{'A':fact('angle ABE','20','30',[174,38,211,63]),'B':fact('angle EDC','60','70',[189,127,228,152])},[
event('A','The angle at B is 20 degrees','20'),event('B','and the angle at D is 60 degrees','60'),event('B','the angle between CD and ED is 60°','60',use_last=True)]),
record(73,'circle_inscribed_central',{'A':fact('angle ABC','70','80',[67,100,105,126])},[
event('A','angle ABC is given as 70 degrees','70'),event('A','in the figure, the angle at B is 70°','70',use_last=True)]),
record(77,'parallel_two_transversals',{'A':fact('angle2','60','70',[43,86,82,115])},[
event('A',"there's a 60° angle between the two transversals",'two transversals','right transversal and upper horizontal line',readout_kind='entity_binding'),event('A','Angle 1 = angle 3 = 60° (given)','1 = angle 3','2',readout_kind='entity_binding')], 'Arrow60 labels angle2. Native places60 between the transversals and later falsely calls angle1/3=60 given. Correct final120 does not fix these local mistakes.'),
record(81,'right_triangle_altitude_bisector',{'A':fact('right-angle ADB marker','90','80',[108,151,126,171],False),'B':fact('angle ABC','50','60',[47,145,90,175]),'C':fact('angle BAC','90','100',[44,69,85,98])},[
event('A','So angle ADB is 90 degrees','90'),event('B','Also, angle at B is 50 degrees','50'),event('C',"the problem mentions a 90° angle near A",'90',use_last=True)], 'SymbolicD90 and numericA90 are distinct sources; A90 is recovered only late in the shown reasoning.'),
record(87,'circle_parallel_chord_diameters',{'A':fact('central angle EOD','50','60',[115,75,156,104])},[
event('A','The angle between OE and OD is given as 50 degrees','50'),event('A','arc AB = arc DE = 50°','AB','DE',readout_kind='entity_binding',use_last=True,correctness='UNDECIDABLE',claim_note='This equality is a derived unsupported chord rule, not a directly observed AB label. Record as demand/integration uncertainty, not a confident visual hallucination.')], 'EOD50 correctly represents the marked arcDE50 aid. Native fails to use the two diameters and invents a chord-central-angle relation. No source-coupled extraction error inferred from wrong final100.',integration_error_reviewed=True,integration_error_quote='the measure of angle BOC is equal to twice the measure of angle EOD.'),
record(88,'circle_radii_base_angles',{'A':fact('angle ACO','42','52',[53,102,83,125]),'B':fact('angle ABO','22','32',[138,109,168,136])},[
event('A','The figure shows angle AOC as 42 degrees','AOC','ACO',readout_kind='entity_binding'),event('B','and angle AOB as 22 degrees','AOB','ABO',readout_kind='entity_binding'),event('A','maybe the problem is that angle AOC is 42°','AOC','ACO',readout_kind='entity_binding',use_last=True)], 'Both labels are at circumference C/B, not O. Center assignments remain wrong even though their numeric values are read correctly.')
]
write_json(OUT/'cohort/review/manual_0030.json',rows)
