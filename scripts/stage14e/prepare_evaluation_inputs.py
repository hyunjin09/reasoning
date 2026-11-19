"""Freeze original512-token anchors and source-only references without final inspection."""
import json,hashlib
from tokenizers import Tokenizer
from scripts.stage14e.common import *
from scripts.stage14d1.contracts import choose_checkpoint,safe_payload
selection=load(P/'manifests/evaluation_family_selection_v1.json');chosen={r['family_id']:r for r in selection['rows']}
inv={r['family_id']:r for r in rows('outputs/stage14d0/inventory/source_and_raw_output_manifest.jsonl') if r['family_id'] in chosen}
cfg=load(P/'protocol/runtime_v1.json');tok=Tokenizer.from_file(str(Path(cfg['model']['model']['checkpoint'])/'tokenizer.json'))
run=[];source=[];provenance=[]
for s in selection['rows']:
 m=inv[s['family_id']];n=m['native']['T'];ip=n['input'];gp=n['generation']
 assert sha(ip)==n['input_sha256'] and sha(gp)==n['generation_sha256'];assert sha(m['image'])==m['image_sha256']
 inp=load(ip);g=load(gp);ids=g['generated_token_ids'][:512];text=tok.decode(ids,skip_special_tokens=True)
 while ids and not g['raw_decoded_response'].startswith(text) and text.endswith('\ufffd'):ids=ids[:-1];text=tok.decode(ids,skip_special_tokens=True)
 assert g['raw_decoded_response'].startswith(text)
 prefix=choose_checkpoint(text,len(text));nt=len(tok.encode(prefix,add_special_tokens=False).ids)
 seed=int(hashlib.sha256(('stage14e-seed-v1|'+m['family_id']).encode()).hexdigest()[:8],16)%(2**31)
 r={'item_id':m['item_id'],'family_id':m['family_id'],'question':m['native_question'],'image':m['image'],'image_sha256':m['image_sha256'],'prefix':prefix,'prefix_sha256':hashlib.sha256(prefix.encode()).hexdigest(),'seed':seed,'eligible':nt>=64,
 'original_chat_prompt':inp['chat_prompt'],'original_messages':inp['messages'],'original_image_pixels':inp['prepared_image_pixel_sha256'],'original_image_sizes':inp['prepared_image_sizes']}
 safe_payload(r);run.append(r)
 source.append({**s,'question':m['native_question'],'E_star_atoms':m['E_star_atoms'],'atom_metadata':m['atom_metadata'],'E_star_sha256':m['E_star_sha256'],'E_star_annotation_path':m['E_star_annotation_path'],'prefix_evaluation_only':prefix})
 provenance.append({'family_id':m['family_id'],'item_id':m['item_id'],'input':ip,'input_sha256':n['input_sha256'],'generation':gp,'generation_sha256':n['generation_sha256'],'prefix_tokens':nt,'prefix_sha256':r['prefix_sha256'],'eligible':r['eligible'],'only_first512_generated_tokens_used':True,'final_answer_or_correctness_inspected':False})
(P/'inference/evaluation_families.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in run))
save(P/'offline/evaluation_source_references_v1.json',source);save(P/'audit/evaluation_input_freeze_v1.json',{'at':now(),'families':provenance,'selection_sha256':sha(P/'manifests/evaluation_family_selection_v1.json'),'runtime_sha256':sha(P/'inference/evaluation_families.jsonl'),'source_reference_sha256':sha(P/'offline/evaluation_source_references_v1.json')})
print('families',len(run),'eligible',sum(r['eligible'] for r in run))
