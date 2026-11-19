import unittest,json,hashlib,shutil
from pathlib import Path
from PIL import Image
from scripts.stage14d1.views import render_views
from scripts.stage14d1.contracts import safe_payload
P=Path('outputs/stage14d1_sava')
def rows(p):return [json.loads(s) for s in p.read_text().splitlines()]
class SourceTests(unittest.TestCase):
 def test_real_cohort_and_ingress(self):
  selected=rows(P/'data/selected_family_target_manifest.jsonl');runtime=rows(P/'inference/families.jsonl')
  self.assertEqual(len({r['family_id'] for r in selected}),72);self.assertEqual(sum(r['technical'] for r in selected),8)
  for c,n in [('global_required',36),('local_sufficient',18),('local_plus_global',18)]:self.assertEqual(sum(r['audit_context_stratum']==c for r in selected),n)
  for r in runtime:
   safe_payload(r);self.assertEqual(hashlib.sha256(r['prefix'].encode()).hexdigest(),r['prefix_sha256'])
   self.assertNotIn('</think>',r['prefix']);self.assertNotIn('\\boxed',r['prefix'])
 def test_crops_preserve_exact_source_and_global(self):
  root=P/'audit/test_views';self.assertFalse(root.exists());root.mkdir()
  try:
   src=root/'source.png';im=Image.new('RGB',(100,50));im.putdata([(i%256,(i//100)%256,7) for i in range(5000)]);im.save(src)
   a={'mode':'LOCAL','boxes':[[.1,.2,.6,.8]],'source_reference':'test','uncertainty':'certain'}
   out=render_views(str(src),a,root/'out');self.assertEqual(out['paths'][0],str(src))
   crop=Image.open(out['paths'][1]);self.assertEqual(crop.size,(50,30));self.assertEqual(crop.tobytes(),im.crop((10,10,60,40)).tobytes())
   a['mode']='GLOBAL';a['boxes']=[];self.assertEqual(render_views(str(src),a,root/'global')['paths'],[str(src)])
  finally:shutil.rmtree(root)
if __name__=='__main__':unittest.main()
