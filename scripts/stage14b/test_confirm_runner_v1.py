"""CPU fault injection for finite confirmation OOM supervision."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.stage14b import common, oom_policy, confirm_runner_v1 as runner

FAKE = r'''
import hashlib,json,os,sys
from pathlib import Path
m=json.loads(Path(sys.argv[1]).read_text());root=Path(m['test_root'])
dest=root/'audit/workers'/os.environ['SLURM_JOB_ID']/'engines'/m['engine_id']
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fp(t):return hashlib.sha256(json.dumps(t,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def folder(t):return root/'raw'/t['collection']/t['task_id']/('attempt_'+str(m['attempts'][t['task_id']]))
if m.get('batch_oom') and m['batch_size']==18:
 for t in m['rows'][:2]:save(folder(t)/'input.json',{})
 save(dest/'failure.json',dict(active_ids=[t['task_id'] for t in m['rows'][:2]],completed=0,phase='step',error='CUDA out of memory'))
 print('CUDA out of memory',flush=True);sys.exit(1)
done=0
for t in m['rows']:
 f=folder(t);save(f/'input.json',{})
 if t['task_id']=='bad':
  error='CUDA illegal memory access' if m.get('non_oom') else 'CUDA out of memory'
  save(dest/'failure.json',dict(active_ids=['bad'],completed=done,phase='step',error=error))
  print(error,flush=True);sys.exit(1)
 save(f/'generation.json',{})
 save(f/'result.json',dict(task_sha256=fp(t),input_sha256=sha(f/'input.json'),generation_sha256=sha(f/'generation.json')))
 done+=1
save(dest/'exit.json',dict(calls=done,complete=True,technical_failures=0))
'''

class ConfirmationRunnerTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir='runs');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
  for mod in (common,oom_policy,runner):
   p=patch.object(mod,'ROOT',self.root);p.start();self.addCleanup(p.stop)
  for name in ('verify_recovery','verify_confirmation','authorize'):
   p=patch.object(runner,name,lambda *a:None);p.start();self.addCleanup(p.stop)
  p=patch.dict(os.environ,SLURM_JOB_ID='fake');p.start();self.addCleanup(p.stop)
  self.engine=self.root/'fake.py';self.engine.write_text(FAKE)
 def execute(self,ids,**kw):
  self.tasks=[dict(task_id=x,collection='test') for x in ids];path=self.root/'manifest.json'
  common.save(path,dict(mode='confirmatory',rows=self.tasks,test_root=str(self.root),**kw))
  runner.run(path,common.sha(path),worker_command=[sys.executable,str(self.engine)],poll_seconds=.01)
 def manifest(self,k):return common.load(self.root/f'audit/workers/fake/engine_{k:04d}_manifest.json')
 def test_healthy_keeps_batch18_and_exits(self):
  self.execute(['a','b']);self.assertEqual(self.manifest(0)['batch_size'],18)
  self.assertTrue(common.load(self.root/'audit/workers/fake/exit.json')['complete'])
 def test_unattributed_batch_oom_retries_interrupted_once_singleton(self):
  self.execute(['a','b','c'],batch_oom=True)
  m=self.manifest(1);self.assertEqual(m['batch_size'],1);self.assertEqual(m['attempts'],{'a':1,'b':1,'c':0})
  for t in self.tasks:self.assertIsNotNone(common.checked_result(t))
 def test_identified_oom_skips_and_continues(self):
  self.execute(['a','bad','c']);self.assertTrue(oom_policy.missing_path(self.tasks[1]).exists())
  self.assertIsNotNone(common.checked_result(self.tasks[2]));self.assertEqual(self.manifest(1)['batch_size'],1)
 def test_non_oom_holds(self):
  with self.assertRaisesRegex(RuntimeError,'non-OOM'):self.execute(['a','bad','c'],non_oom=True)
  self.assertFalse(oom_policy.missing_path(self.tasks[1]).exists());self.assertFalse(common.result_dir(self.tasks[2]).exists())
 def test_batch_retry_oom_skips_no_third_attempt(self):
  self.execute(['bad','b','c'],batch_oom=True)
  self.assertTrue(oom_policy.missing_path(self.tasks[0]).exists())
  self.assertFalse(common.result_dir(self.tasks[0],2).exists());self.assertIsNotNone(common.checked_result(self.tasks[2]))

if __name__=='__main__':unittest.main()
