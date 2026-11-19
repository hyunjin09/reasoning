import os,subprocess,sys,unittest
from pathlib import Path

class WorkerImportTests(unittest.TestCase):
    def test_script_directory_does_not_shadow_standard_statistics(self):
        root=Path(__file__).resolve().parents[2]
        env=dict(os.environ,PYTHONPATH=str(root/'code')+os.pathsep+str(root))
        result=subprocess.run([sys.executable,'-c','from statistics import median; assert median([1,3,2]) == 2'],
            cwd=root/'scripts/stage11a',env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
