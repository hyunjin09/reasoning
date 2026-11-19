"""Score-blind image/native review, screen positions140–149."""
from scripts.stage5a.annotate_batch_0010 import fact,event,record
from scripts.stage5a.prepare import OUT,write_json
def bearing(b,a,z,events,notes='',**kw):
 return record(b,'bearing_triangle_cardinal_reference',{'A':fact('angle BAC from east',a,str(int(a)+10),[66,62,137,115]),'B':fact('angle ABC from west',z,str(int(z)+10),[215,64,284,115])},events,notes,evidence_type='direction_and_angle',**kw)
rows=[
record(335,'bearing_single_southwest_ray',{'A':fact('ray OA southwest','southwest','southeast',[90,195,186,309],False),'B':fact('angle OA from south','32','42',[137,240,173,270])},[
event('A','point A is somewhere in the southwest direction','southwest',readout_kind='spatial_orientation'),event('B','The angle given is 32 degrees','32'),event('B','If OA is 32° west of south','32',use_last=True)],'RayAiswestofsouth; allselectedpremisescorrect.',evidence_type='direction_and_angle'),
record(336,'bearing_single_northwest_ray',{'A':fact('ray OA northwest','northwest','northeast',[80,37,182,195],False),'B':fact('angle OA from north','31','41',[146,117,178,140])},[
event('A','point A is somewhere in the northwest direction relative to O','northwest',readout_kind='spatial_orientation'),event('B','the line OA is 31 degrees','31'),event('B','a point is 31° west of north','31',use_last=True)],'Northreferenceand31correct; earliestlocalizedraydirectionretained.',evidence_type='direction_and_angle'),
bearing(337,'37','48',[
event('A',"Point A has a 37° angle from the north towards the east?",'north','east',readout_kind='entity_binding',correctness='UNDECIDABLE'),event('B',"at point B, there's a 48° angle between the north arrow and the line to C",'north','west',readout_kind='entity_binding'),event('B','The 48° at B is probably irrelevant for this particular question','48',use_last=True,semantic_role='MENTION_ONLY')],'37liesbetweenABeastandAC;48betweenBAwestandBC. Neitherisnorthreference. Late48existencecorrect andexplicitlyirrelevant to due-west bearingBA; no falsereadoutbindingrepairfornumericmention.'),
bearing(338,'49','39',[
event('A',"at point A, there's a 49° angle between the north direction and the line from A to C",'north','east',readout_kind='entity_binding'),event('B',"at point B, there's a 39° angle between the north direction and the line BC",'north','west',readout_kind='entity_binding'),event('A','the angle between north (up) and AC is 49°','north (up)','east (right)',readout_kind='entity_binding',use_last=True)],'Repeatednorthreferenceerrorratherthannumericmisreading.'),
bearing(339,'49','41',[
event('A','The angle between the North direction at A and the line AB is given as 49 degrees','North direction at A and the line AB','east direction at A and the line AC',readout_kind='entity_binding'),event('B',"why is there a 41° angle at B?",'41',semantic_role='MENTION_ONLY',use_last=True)],'First49claimmisidentifiesbothreferenceandray; repairtargetswholepair. Onlytwodistinctevents: lastvisualB41mentionisalsofirstselectedchangedsource; do notduplicateit.'),
bearing(340,'45','37',[
event('A','The angles given are 45° at point A and 37° at point B','45'),event('B','The angles given are 45° at point A and 37° at point B','37'),event('B','Since at point B, the angle between north and BC is 37°','north','west',readout_kind='entity_binding',use_last=True)],'Image45/37 overridesTD49/41; final53correct despite latewrongnorthreference.',dataset_discrepancy='TDaid49/41 differsactualimage45/37; truthusesimage.'),
bearing(341,'42','53',[
event('A','The angles given are 42° at A and 53° at B','42'),event('B','The angles given are 42° at A and 53° at B','53'),event('A','the angle marked is 42°, between north and the dashed line AC','north','east',readout_kind='entity_binding',use_last=True)],'Correctinitialnumericlocations; latevisualnorthreferencewrong.'),
bearing(342,'38','49',[
event('A','Point A has a 38° angle between the north direction and the line from A to C','north','east',readout_kind='entity_binding'),event('B',"at point B, there's a 49° angle between the north direction and the line from B to C",'north','west',readout_kind='entity_binding'),event('B','If BC is 49° east of north','east of north','south of west',readout_kind='entity_binding',correctness='UNDECIDABLE',use_last=True)],'A38fromeast,B49fromwesttowardsouth; conditionalfinaldirectionclaimwrongbutuncertain.'),
record(347,'tree_elevation_height',{'A':fact('lower right elevation angle','43','53',[271,190,307,217]),'B':fact('horizontal distance','20','22',[186,226,235,249]),'C':fact('height variable','h','x',[78,109,100,146],False)},[
event('A',"There's a 43-degree angle at the bottom right",'43'),event('B','the base of the triangle is 20 meters','20'),event('B','the right triangle has a 43° angle, base 20m, height h','20',use_last=True)],'43and20correct. Treeiconhypothesesnotdirectnumericpremiseerrors.',evidence_type='angle_and_length_labels'),
record(348,'helicopter_depression_distance',{'A':fact('upper left depression angle','44','54',[166,114,205,139]),'B':fact('vertical altitude','198','188',[423,200,480,226])},[
event('A','one angle being 44 degrees','44'),event('B','the side opposite to the 44-degree angle is 198 meters','198'),event('B','the side opposite is the vertical side (198m)','198',use_last=True)],'44angleand198oppositelegcorrect.',evidence_type='angle_and_length_labels')
]
write_json(OUT/'cohort/review/manual_0140.json',rows)
