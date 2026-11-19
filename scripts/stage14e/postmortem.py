"""Read-only joins over sealed SAVA evidence; all products go to a new cycle."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
OLD=Path('outputs/stage14d1_sava_pilot/v1')
NEW=Path('outputs/stage14e_acquisition_development/v1')
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 seal=load(OLD/'audit/final_closure_seal_v8.json'); bad=[p for p,h in seal['files'].items() if sha(p)!=h]
 assert not bad,bad
 save(NEW/'audit/historical_preservation_initial.json',{'files_verified':len(seal['files']),'seal_sha256':sha(OLD/'audit/final_closure_seal_v8.json'),'mismatches':bad})
 families=[json.loads(l) for l in (OLD/'inference/families.jsonl').read_text().splitlines()]
 design=load(OLD/'manifests/resumption_v8_design.json');scores=load(OLD/'analysis/scored_logical_rows_final_v8.json')['rows']
 docs=[]
 for f in sorted(families,key=lambda x:int(x['item_id'])):
  i=f['item_id'];sp=Path(design['source_states'][i]);a=load(sp)
  q=load(OLD/f'annotations/query_only/{i}.json');loc=load(OLD/f'annotations/address_only/{i}.json');rp=OLD/f'annotations/readouts/{i}.json'
  docs.append(dict(**f,acquisition=a,acquisition_path=str(sp),acquisition_sha256=sha(sp),query_review=q,address_review=loc,
                   readout_review=load(rp) if rp.exists() else None,solver_rows=[s for s in scores if s['item_id']==i]))
 assert len(docs)==len({r['family_id'] for r in docs})==72
 save(NEW/'analysis/sava72_joined.json',docs)
 chunks=[]
 for r in docs:
  q=r['query_review'];a=r['acquisition'];read=a.get('readouts',{}).get('QI',{}).get('value')
  chunks.append(f"ID {r['item_id']}\nQUESTION {r['question']}\nQUERY {a['query']}\nREVIEW {q['label']} / {q['notes']}\nADDRESS {r['address_review']['label']} / {r['address_review']['notes']}\nPREFIX_END {r['prefix'][-700:]}\nQI {read}\n")
 for k in range(6):
  (NEW/f'analysis/postmortem_packet_{k}.txt').write_text('\n'.join(chunks[k*12:(k+1)*12]))
  sheet=Image.new('RGB',(1800,1620),'#eeeeee');draw=ImageDraw.Draw(sheet)
  for j,r in enumerate(docs[k*12:(k+1)*12]):
   im=Image.open(r['image']).convert('RGB'); im.thumbnail((440,500));x=(j%4)*450;y=(j//4)*540
   sheet.paste(im,(x+(450-im.width)//2,y+30+(500-im.height)//2));draw.text((x+10,y+8),'ID '+r['item_id'],fill='black')
  sheet.save(NEW/f'analysis/source_sheet_{k}.jpg',quality=95)
 print('verified',len(seal['files']),'joined',len(docs))
if __name__=='__main__':main()
