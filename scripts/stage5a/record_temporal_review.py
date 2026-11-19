"""Record the manually read complete short native prefixes; never infer ABA order."""
from scripts.stage5a.prepare import OUT,read_json,read_jsonl,write_json,sha
from visual_reasoning.stage5a.annotation import temporal_annotation

ledger=read_json(OUT/'cohort/review/temporal_review_ledger.json')
rows=[r for p in sorted((OUT/'annotations').glob('provisional_manual_*.jsonl')) for r in read_jsonl(p)]
by={e['event_id']:(r,e) for r in rows for e in r['events']}
reviewed=['10','14','17','29','56','87','91','94','99','114','115','174','177','195','198','200','209','210','223','224','240','245','246','414']
errors=[]

def add(key,role,previous,quote='',note=''):
    r,e=by[key];b=key.split('_')[0];packet=OUT/f'cohort/review/temporal_full_{reviewed.index(b)//6*6:04d}.md'
    value={'full_native_prefix_reviewed':True,'role':role,'prior_explicit_availability':role!='FIRST_USE',
           'previous_source':previous,'evidence_quote':quote,'review_packet':str(packet.relative_to(OUT)),
           'review_packet_sha256':sha(packet),'note':note,
           'availability_scope':'Prior native source-associated premise, including wrong extraction/binding; does not assert earlier correct grounding.'}
    try:temporal_annotation({**e,'temporal_review':value},e['history_before_ed_text'])
    except ValueError as error:errors.append(f'{key}: {quote!r}: {error}')
    ledger[key]=value

for b in ['10','14','29','56','87','91','99']:
    r,e=by[b+'_E2']
    quote={'91':"the figure has a 30° angle at A",'99':'Angle CAD is 26 degrees.'}.get(b,r['events'][0]['quote'])
    add(b+'_E2','REUSE_WITHOUT_INTERVENING_SOURCE','A',quote)
add('17_E2','FIRST_USE','A')
add('17_E3','REUSE_WITHOUT_INTERVENING_SOURCE','A',"At point A, there's a 42° angle between AD and AC",'An unselected A re-reading already precedes this readout; selected A/B/A order alone would mislabel refresh.')
add('94_E2','FIRST_USE','A')
add('94_E3','REUSE_WITHOUT_INTERVENING_SOURCE','B','CE is 6 units.')
add('114_E2','FIRST_USE','A')
add('114_E3','REFRESH_AFTER_OTHER_SOURCE','B','full circle with radius 1','A90 was explicit first; B radius1 is the last separately invoked numeric visual premise before this return to A.')
add('115_E2','FIRST_USE','A')
add('115_E3','REUSE_WITHOUT_INTERVENING_SOURCE','A','full circle with radius 6','Unselected radius6 use follows the latest120-degree use; this is not a new A/B/A refresh.')
add('174_E3','REUSE_WITHOUT_INTERVENING_SOURCE','B','Similarly, angle at D is 65°, which is angle ADC = 65°.')
add('177_E2','FIRST_USE','A')
add('198_E2','FIRST_USE','A+B')
add('198_E3','REUSE_WITHOUT_INTERVENING_SOURCE','C','The base is 10, height is 12.')
add('200_E2','FIRST_USE','C')
add('200_E3','REUSE_WITHOUT_INTERVENING_SOURCE','B',"There's a 54-degree angle at the base")
add('210_E2','FIRST_USE','A')
add('210_E3','REUSE_WITHOUT_INTERVENING_SOURCE','C','and DE = 5.')
add('223_E2','FIRST_USE','A')
add('223_E3','REFRESH_AFTER_OTHER_SOURCE','B','(3√2)² = 18.','The unselected radical-square calculation reuses B immediately before current A squared; prior A5 is explicit.')
add('224_E2','REUSE_WITHOUT_INTERVENING_SOURCE','A',"That's six vertices.")
add('240_E2','FIRST_USE','A')
add('240_E3','REFRESH_AFTER_OTHER_SOURCE','B','(3y + 40)°','C expression appeared earlier; the full current list explicitly revisits A then B before returning to C.')
add('245_E2','REFRESH_AFTER_OTHER_SOURCE','A',"there's a segment labeled x + 9 next to point G",'B formula was already explicit; the last identified source is A at G, not the previous selected-event sequence alone.')
add('246_E2','REUSE_WITHOUT_INTERVENING_SOURCE','A','The length of that line is 6.2 cm.')
add('246_E3','REUSE_WITHOUT_INTERVENING_SOURCE','A','diameter is 6.2 cm.')
add('414_E2','FIRST_USE','A')
add('414_E3','REUSE_WITHOUT_INTERVENING_SOURCE','B','The sector is 23/360 of that','Reuse of the incorrectly extracted sector premise; no prior correct337-degree premise is established.')

for key in ['174_E2','177_E3','195_E2','195_E3']:
    ledger[key]={'full_native_prefix_reviewed':False,'manual_prefix_inspected':True,
                 'unresolved_reason':'Joint/equal-valued source mentions prevent unique previous-source identity; do not choose one from selected-event order.'}
if errors:raise ValueError(errors)
write_json(OUT/'cohort/review/temporal_review_ledger.json',ledger)
print({'reviewed_entries':len(ledger),'resolved':sum(v['full_native_prefix_reviewed'] for v in ledger.values())})
