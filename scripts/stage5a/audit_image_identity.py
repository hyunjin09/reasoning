"""Score-blind decoded-image identity and rescale proposals; no causal features."""
import hashlib
from collections import defaultdict
from PIL import Image,ImageChops
from scripts.stage5a.prepare import ROOT,OUT,read_json,write_json
from visual_reasoning.stage0.data import load_mathverse_rows,resolve_image_path

cfg=read_json(OUT/'config/stage5a_config.json')
prior=set(read_json(OUT/'config/cohort_rules.json')['prior_excluded_bases'])
groups=defaultdict(list);thumbs=[]
for r in load_mathverse_rows(__import__('pathlib').Path(cfg['dataset_root'])):
 if r['problem_version']!='Vision Dominant':continue
 b=str(r['problem_index']);path=resolve_image_path(__import__('pathlib').Path(cfg['dataset_root']),r['image'])
 with Image.open(path) as im:
  im=im.convert('RGB');digest=hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest()
  groups[digest].append(b)
  diff=ImageChops.difference(im,Image.new('RGB',im.size,'white'));box=diff.getbbox()
  small=im.crop(box).convert('L').resize((17,16))
  vals=list(small.getdata());bits=sum((vals[y*17+x]>vals[y*17+x+1])<<(y*16+x) for y in range(16) for x in range(16))
  thumbs.append((b,digest,bits))
exact=[{'bases':sorted(bs,key=int),'prior_bases':sorted(set(bs)&prior,key=int)} for bs in groups.values() if len(bs)>1]
proposals=[]
for i,(b,d,h) in enumerate(thumbs):
 for c,e,k in thumbs[:i]:
  if d!=e and (b not in prior or c not in prior) and (h^k).bit_count()<=4:
   proposals.append({'bases':[c,b],'dhash_distance':(h^k).bit_count(),'status':'requires_visual_comparison'})
write_json(OUT/'cohort/review/decoded_image_identity_audit.json',{'score_blind':True,'images':len(thumbs),'exact_decoded_groups':exact,'rescale_proposals':proposals})
print({'exact_decoded_groups':exact,'rescale_proposals':proposals})
