"""Run the finite scientific queue with an independent CPU allocation guard."""
import argparse,subprocess,sys
from scripts.stage14e.evaluation_worker_v2 import run
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('manifest');a=p.parse_args()
 guard=subprocess.Popen([sys.executable,'-m','scripts.stage14e.resource_guard',a.manifest])
 try:run(a.manifest)
 finally:
  guard.terminate()
  try:guard.wait(timeout=5)
  except subprocess.TimeoutExpired:guard.kill();guard.wait()
