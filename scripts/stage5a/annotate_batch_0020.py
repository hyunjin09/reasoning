"""Human score-blind review for screen positions20–29."""
from scripts.stage5a.annotate_batch_0010 import fact,event,record
from scripts.stage5a.prepare import OUT,write_json
rows=[
record(45,'circle_inscribed_central',{'A':fact('angle ACB','35','45',[156,81,192,111])},[
event('A','The given information is that angle OCB is 35 degrees','OCB','ACB',readout_kind='entity_binding'),event('A','Angle OCB = 35°, so angle OBC','OCB','ACB',readout_kind='entity_binding',use_last=True)], 'The chord is AC; no radiusOC is drawn. Native calls the marked inscribed angle OCB, a wrong source binding, even though the final70 is correct.'),
record(48,'circle_major_minor_arc',{'A':fact('minor central angle BOC','100','110',[98,128,154,159])},[
event('A',"There's an angle at O, which is 100 degrees, labeled as angle BOC",'100'),event('A','The central angle BOC is 100°, so arc BC is 100°','100',use_last=True)], 'The label100 is correctly read. A lies on the minorBC arc, so BAC intercepts the major260 arc. Native final50 uses the wrong intercepted arc despite local numeric correctness.',integration_error_reviewed=True,integration_error_quote='The central angle BOC is 100°, so arc BC is 100°. Angle BAC intercepts arc BC, so it\'s half of that, 50°.'),
record(49,'cyclic_pentagon',{'A':fact('angle CAD','30','40',[425,283,560,376]),'B':fact('angle AED','115','125',[578,350,739,433])},[
event('A',"there's a 30° angle at A",'30'),event('B','and a 115° angle at E','115'),event('B','the measure of angle AED = 115°','115',use_last=True)], 'IMAGE/TEXT discrepancy: VD image visibly prints30 at CAD while Text-Dominant aid says35. Image-local truth is30. Initial generic A30 location is correct; later BAC/CAD hypotheses are not the selected first claim. Global answer grading retains benchmark status without using it to repair local truth.',dataset_discrepancy='TD CAD35 versus source image CAD30'),
record(50,'intersecting_lines_perpendicular_ray',{'A':fact('angle BOD','50','60',[182,125,232,157]),'B':fact('right-angle AOE','90','80',[136,113,165,142],False)},[
event('A','Also, angle EOD is 50 degrees','EOD','BOD',readout_kind='entity_binding'),event('B','a small square, indicating 90 degrees','90'),event('A','D is such that angle EOD = 50°','EOD','BOD',readout_kind='entity_binding')], 'First broad right-angle mention lacks a numeric readout but is logged here; the first atomic50 is assigned to EOD instead of BOD. Right-angle square establishes AOE90 and is a distinct source.'),
record(53,'parallel_transversal',{'A':fact('angle1','55','65',[176,7,224,41])},[
event('A','The diagram shows angle 1 with a 55° angle marked next to it','55'),event('A',"The diagram shows angle 1 with a 55° angle next to it",'55',use_last=True)], 'The arrow labels angle1 itself. The first visual numeric mention is correct but later adjacency speculation leads to a wrong supplementary solution. Numeric correctness does not validate its subsequent binding hypothesis.'),
record(54,'ruler_right_triangle',{'A':fact('angle1','40','50',[56,6,95,39]),'B':fact('triangle right-angle marker','90','80',[117,28,143,54],False)},[
event('A',"there's a 40-degree angle mentioned",'40'),event('B',"Let's assume it's a right-angled triangle with angles 90°, 40°, and 50°",'90',correctness='UNDECIDABLE'),event('A','it forms a 40° angle with one side','40',use_last=True)], '40 labels the ruler/triangle intersection, not a triangle corner. The initial direct number and later ruler-side40 are correct; the middle proposed full triangle angle triple is explicitly hypothetical, so local90 assignment remains undecidable.'),
record(55,'angle_bisector_perpendicular_rays',{'A':fact('angle AOC','70','80',[54,108,102,141]),'B':fact('OM perpendicular ON marker','90','80',[112,76,137,101],False)},[
event('A','which is angle AOM, I think','AOM','AOC',readout_kind='entity_binding',correctness='UNDECIDABLE'),event('A','Angle AOM is 70°, so angle MON','AOM','AOC',readout_kind='entity_binding',use_last=True)], 'Arrow70 covers AOC, bisected by OM. First AOM identification is tentative; late assertion AOM70 is wrong. The second source square is recorded but no unambiguous explicit90 claim at that source is selected.'),
record(56,'circle_diameter_chord_midpoint',{'A':fact('angle DCF','20','30',[116,84,151,110])},[
event('A',"there's angle C (at point C) which is 20 degrees",'20'),event('A','angle ECO = 20°','ECO','FCO',readout_kind='entity_binding',use_last=True)], '20 is C between CD/CF. Native later references unpictured CE but symmetry makes ECO20 mathematically valid if CE is constructed: mark that late statement as a derived demand, not a directly seen chord.',derived_event_ids=['E2']),
record(58,'parallel_right_triangle',{'A':fact('angle AEC','35','45',[119,54,157,78]),'B':fact('angle CED','90','100',[156,66,194,93])},[
event('A',"There's a 35° angle at E between AB and EC",'35'),event('B','and a 90° angle at E between EC and ED','90'),event('B','If angle at E is 90°, then angle at C (35°)','90',use_last=True)]),
record(59,'parallel_angle_bisector',{'A':fact('angle ACD','80','90',[47,163,96,196])},[
event('A',"There's a 80-degree angle at C",'80'),event('A','angle at C: angle ACD = 80°','80')], 'Native corrects an early alternate-interior hypothesis and reaches50. Selected direct80 claims are correct.')
]
# ECO20 follows chord symmetry and is mathematically true; it is not a false visual fact.
rows[7]['events'][1]=event('A','angle at C is given as 20 degrees','20',use_last=True)
write_json(OUT/'cohort/review/manual_0020.json',rows)
