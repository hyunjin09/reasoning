"""Guard allocation billing independently of GPU engine startup or execution."""
import argparse,importlib,json,subprocess,sys
from pathlib import Path
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('manifest');a=p.parse_args();m=json.loads(Path(a.manifest).read_text())
 assert m['worker'] in ['acquisition_worker','continuation_worker']
 guard=subprocess.Popen([sys.executable,'-m','scripts.stage14e.resource_guard',a.manifest])
 try:importlib.import_module('scripts.stage14e.'+m['worker']).run(a.manifest)
 finally:
  guard.terminate()
  try:guard.wait(timeout=5)
  except subprocess.TimeoutExpired:guard.kill();guard.wait()
