"""CPU-only subprocess fault injection: OOM -> skip -> next sample completion."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.stage14b import common, oom_policy, oom_runner


FAKE_ENGINE = r'''
import hashlib,json,os,sys
from pathlib import Path
m=json.loads(Path(sys.argv[1]).read_text());root=Path(m['test_root'])
job=os.environ['SLURM_JOB_ID'];dest=root/'audit/workers'/job/'engines'/m['engine_id']
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fp(t):return hashlib.sha256(json.dumps(t,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
done=0
for t in m['rows']:
 folder=root/'raw'/t['collection']/t['task_id']/('attempt_'+str(m['attempts'][t['task_id']]))
 save(folder/'input.json',{})
 if t['task_id']=='bad':
  error='CUDA out of memory' if not m.get('non_oom') else 'CUDA illegal memory access'
  save(dest/'failure.json',dict(active_ids=['bad'],completed=done,phase='step',error=error))
  print(error,flush=True);sys.exit(1)
 save(folder/'generation.json',{})
 save(folder/'result.json',dict(task_sha256=fp(t),input_sha256=sha(folder/'input.json'),generation_sha256=sha(folder/'generation.json')))
 done+=1
save(dest/'exit.json',dict(calls=done,complete=True,technical_failures=0))
'''


class OOMRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir='runs');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()
        for mod in (common,oom_policy,oom_runner):
            p=patch.object(mod,'ROOT',self.root);p.start();self.addCleanup(p.stop)
        for name in ('verify_recovery','authorize'):
            p=patch.object(oom_runner,name,lambda *args:None);p.start();self.addCleanup(p.stop)
        p=patch.dict(os.environ,SLURM_JOB_ID='fake_cpu_job');p.start();self.addCleanup(p.stop)
        self.engine=self.root/'fake_engine.py';self.engine.write_text(FAKE_ENGINE)
        self.tasks=[dict(task_id=x,collection='cpu_test') for x in ('first','bad','next')]

    def execute(self,non_oom=False):
        path=self.root/'manifest.json'
        common.save(path,dict(rows=self.tasks,recovery_of='original',test_root=str(self.root),non_oom=non_oom))
        oom_runner.run(path,common.sha(path),worker_command=[sys.executable,str(self.engine)],poll_seconds=0.01)

    def test_fatal_oom_skips_bad_sample_and_finishes_next_in_fresh_process(self):
        self.execute()
        self.assertIsNotNone(common.checked_result(self.tasks[0]))
        self.assertIsNone(common.checked_result(self.tasks[1]))
        self.assertIsNotNone(common.checked_result(self.tasks[2]))
        self.assertEqual(common.load(oom_policy.missing_path(self.tasks[1]))['reason'],'OOM_SKIP')
        self.assertEqual(len(list(common.result_dir(self.tasks[0]).parent.glob('attempt_*'))),1)
        dest=self.root/'audit/workers/fake_cpu_job'
        self.assertEqual(len(list((dest/'engines').iterdir())),2)
        self.assertTrue(common.load(dest/'exit.json')['queue_exhausted'])

    def test_unrelated_cuda_error_stops_without_skipping_or_advancing(self):
        with self.assertRaisesRegex(RuntimeError,'non-OOM'):
            self.execute(non_oom=True)
        self.assertFalse(oom_policy.missing_path(self.tasks[1]).exists())
        self.assertFalse(common.result_dir(self.tasks[2]).exists())


if __name__=='__main__':unittest.main()
