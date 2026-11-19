"""Start the independent allocation-budget guard before model startup."""
import argparse
import subprocess
import sys
from scripts.stage14e2.worker import run

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest')
    args = parser.parse_args()
    guard = subprocess.Popen([sys.executable, '-m', 'scripts.stage14e.resource_guard', args.manifest])
    try:
        run(args.manifest)
    finally:
        guard.terminate()
        try:
            guard.wait(timeout=5)
        except subprocess.TimeoutExpired:
            guard.kill()
            guard.wait()
