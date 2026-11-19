import subprocess
import sys
import unittest

class ImportSafetyTests(unittest.TestCase):
    def test_worker_script_directory_does_not_shadow_stdlib(self):
        code="import sys;sys.path.insert(0,'scripts/stage14b');from statistics import median;assert median([1,2,3])==2"
        r=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)

if __name__=='__main__':unittest.main()
