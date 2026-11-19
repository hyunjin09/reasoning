"""Hash prior Stage12/13 evidence, without opening outcomes for interpretation."""
import subprocess
from scripts.stage14a.common import ROOT, Path, save, sha, now

def main():
    paths=subprocess.check_output(['rg','--files','--hidden','outputs','reports','scripts'],text=True).splitlines()
    paths=sorted(p for p in paths if any('/stage'+n in p for n in ['12','13']) and '__pycache__' not in p)
    files={p:sha(p) for p in paths}
    save(ROOT/'audit/prior_stage12_13_preservation.json',dict(at=now(),files=files,mode='read-only checksums; no outcome interpretation'))
    print('PRESERVED',len(files),'files')

if __name__=='__main__':main()
