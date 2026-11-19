"""Score-blind image/native review, screen positions170–179."""
from scripts.stage5a.annotate_batch_0010 import fact,event,record
from scripts.stage5a.prepare import OUT,write_json
rows=[
record(388,'circle_radius_circumference',{'A':fact('radius','18','20',[248,151,321,187])},[
event('A','The problem shows a circle with a radius of 18 cm','18'),event('A','The problem says the radius is 18 cm','18',use_last=True)],'Radialarrowstartscenter;18cmcorrect. Samecircletemplatewithdifferentnumbersisnotduplicatestimulus.',evidence_type='length_label'),
record(390,'circle_circumference_to_radius',{'A':fact('circumference','44','46',[282,71,352,102])},[
event('A','they gave a length of 44 cm','44',semantic_role='MENTION_ONLY'),event('A','if we take C = 44 cm','44',use_last=True)],'Circumferentialarrows44,notradius/diameter. Numericlocalpremisescorrect.',evidence_type='length_label'),
record(391,'circle_circumference_to_diameter',{'A':fact('circumference','42','44',[236,59,301,90])},[
event('A','they gave a length of 42 meters','42',semantic_role='MENTION_ONLY'),event('A','Given that the circumference C is 42 meters','42',use_last=True)],'ImageunitmoverridesTDcm. Lastdirectgivenstatementearly;later42arithmeticappearancesdonotaddanewvisualclaim.',evidence_type='length_label',dataset_discrepancy='TDcmvsactual42m; useimageunitm.'),
record(392,'quarter_circle_perimeter',{'A':fact('quarter sector geometry','quarter-circle','semicircle',[50,6,242,204],False),'B':fact('radius','10','12',[138,230,222,268])},[
event('A',"It says it's a quarter-circle, right",'quarter-circle',readout_kind='shape'),event('B','the two straight sides are each 10 mm','10'),event('B','Then two radii: 10 + 10 = 20 mm','10',use_last=True,semantic_role='CURRENTLY_DEMANDED',has_explicit_visual_claim=False)],'Equalradiusticksgiveboth10fromoneprintedlabel;sourceBsinglelabelsemanticCFaffectsbothderivedradii.',evidence_type='shape_and_length'),
record(393,'circle_radius_area',{'A':fact('radius','6','8',[266,161,325,197])},[
event('A','the diagram shows a circle with a radius labeled as 6 cm','6'),event('A','radius r is 6 cm','6',use_last=True)],'6center-to-edgearrowcorrect;lateeligibleexplicitradiusstatementprecedeslongnumericpiwork.',evidence_type='length_label'),
record(394,'three_quarter_circle_area',{'A':fact('circle with quarter missing','quarter missing','half missing',[103,12,588,498],False),'B':fact('radius','2','3',[371,132,419,157])},[
event('A','a shape that looks like a circle with a quarter missing','quarter missing',readout_kind='shape'),event('B','the radius is given as 2 cm','2'),event('B','The diagram shows a 2 cm label','2',use_last=True)],'Initialmissingquarterandradius2correct. Interveningnativeinterpretsremainingfigureasquartersectorandgetswrongarea; notanintegration-onlydiagnosisbecauseanunselectedvisualshapeclaimiswrong.',evidence_type='shape_and_length'),
record(395,'circle_radius_area',{'A':fact('radius','3','5',[260,167,322,202])},[
event('A','a diagram with a radius labeled as 3 cm','3'),event('A','The radius is 3, so squared is 9','3',use_last=True)],'3cmradiallabelcorrect; samedrawingfamily as6/18withdifferentnumericcontent.',evidence_type='length_label'),
record(396,'circle_radius_area',{'A':fact('radius','11','13',[247,188,324,219])},[
event('A','the diagram shows a circle with a radius labeled as 11 cm','11'),event('A','The diagram confirms the radius is 11 cm','11',use_last=True)],'Radial11correct.',evidence_type='length_label'),
record(397,'circle_radius_area',{'A':fact('radius','50','52',[287,158,357,192])},[
event('A','the diagram shows a circle with a radius labeled as 50 cm','50'),event('A','The diagram confirms the radius is 50 cm','50',use_last=True)],'Radial50correct.',evidence_type='length_label'),
record(398,'circle_fractional_radius_area',{'A':fact('radius fraction','1/5','2/5',[280,149,365,203],False)},[
event('A','the image shows a circle with a radius labeled as 1/5 cm','1/5'),event('A','The problem says the radius is 1/5 cm, so that\'s correct','1/5',use_last=True)],'Stackedfraction1/5cmradiallabelcorrect. Existingnumericrendererdoesnotvalidatefractionlayout; CFunavailable.',evidence_type='fractional_length_label')
]
write_json(OUT/'cohort/review/manual_0170.json',rows)
