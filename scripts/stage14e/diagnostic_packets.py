"""Freeze diagnostic raw receipts and source-only review packets after completion."""
import json
from PIL import Image,ImageDraw
from scripts.stage14e.common import *
root=P/'raw/diagnostic_v1c'
assert load(root/'result.json')['status']=='COMPLETED'
m=load(P/'manifests/diagnostic_v1c.json');execution=load(root/'read_execution_manifest.json')['logical']
rawfiles={str(p):sha(p) for p in root.rglob('*.json') if 'snapshot_history' not in str(p) and p.name not in ['allocation_progress.json','progress.json']}
save(P/'audit/diagnostic_raw_freeze_v1.json',{'at':now(),'files':rawfiles})
old={r['item_id']:r for r in load(P/'analysis/sava72_joined.json')};sources={r['item_id']:r for r in rows('outputs/stage14d1_sava_pilot/v1/data/offline_source_manifest.jsonl')}
refs={r['item_id']:r['E_star_atoms'] for r in rows('outputs/stage14d0/inventory/source_and_raw_output_manifest.jsonl')}
qs=load(root/'demand_states.json');locs=load(root/'target_locations.json');targets=load(P/'inference/diagnostic_target_identities.json');ot=load(P/'inference/original_targets.json')
for k in range(4):
 ids=m['families'][k*6:(k+1)*6];text=[];sheet=Image.new('RGB',(1800,1100),'#eee');draw=ImageDraw.Draw(sheet)
 for j,i in enumerate(ids):
  r=old[i];im=Image.open(r['image']).convert('RGB');im.thumbnail((580,490));x=j%3*600;y=j//3*550;sheet.paste(im,(x+(600-im.width)//2,y+30+(500-im.height)//2));draw.text((x+10,y+8),i,fill='black')
  text.append(f"ID {i}\nQUESTION {r['question']}\nSOURCE {refs[i]} / {sources[i]['audit_context_stratum']}\nPREFIX {r['prefix']}\nOLDTARGET {ot[i]}\nNEWTARGET {qs[i]}\nORACLETARGET {targets[i]}\nLOCATION {locs[i]}\n")
  for t in [t for t in execution if t['item_id']==i]:
   text.append(t['condition']+' '+t['status']+' '+(load(t['generation_path'])['raw_decoded_response'] if t['generation_path'] else 'NO READOUT')+'\n')
 (P/f'analysis/diagnostic_review_packet_{k}.txt').write_text('\n'.join(text));sheet.save(P/f'analysis/diagnostic_source_sheet_{k}.jpg',quality=95)
print('frozen',len(rawfiles),'logical',len(execution))
