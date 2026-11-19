from scripts.stage14a.finalize_sources import effective_accepts,history_rows

def test_qc_rejection_and_duplicate_conserve_screened_rows():
 rows=[dict(rank=1,item_id='1',family_id='a',decision='ACCEPT'),dict(rank=2,item_id='2',family_id='b',decision='ACCEPT'),dict(rank=3,item_id='3',family_id='c',decision='ACCEPT'),dict(rank=4,item_id='4',family_id='d',decision='EXCLUDE',exclusion_reason='TEXT_SUFFICIENT')]
 final,ds=effective_accepts(rows,{'1':dict(eligibility='FAIL',exclusion_reason='TEXT_SUFFICIENT')},{'a':'a','b':'b','c':'b','d':'d'})
 assert list(final)==['b'] and final['b']['item_id']=='2'
 assert [r['disposition'] for r in ds]==['EXCLUDE','ACCEPT','ALIAS_ALREADY_ACCEPTED','EXCLUDE']
 assert rows[0]['decision']=='ACCEPT' # primary evidence immutable

def test_catalog_is_exposure_but_not_outcome_review_and_aliases_propagate():
 records=[dict(mathvision_ids=['1'],kind='SOURCE_CATALOG',stage='catalog'),dict(mathvision_ids=['2'],kind='TRACE_REVIEW_ARTIFACT',stage='audit',technical_behavior_review=True)]
 rows=history_rows({'a':['1'],'b':['2','3'],'c':['4']},records,'mathvision');a,b,c=rows
 assert a['historically_exposed'] and not a['outcome_inspection_evidence'] and a['exposure_group']=='SOURCE_ONLY'
 assert b['outcome_inspection_evidence'] and b['technical_exposure_evidence']
 assert b['family_expanded_item_provenance']['3']==[] # group membership not fabricated direct evidence
 assert c['status']=='HISTORICALLY_UNTOUCHED'
