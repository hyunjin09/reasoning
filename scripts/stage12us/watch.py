"""Finite observational watcher; no launch/retry authority."""
import argparse
import re
import subprocess
import time
from pathlib import Path
from scripts.stage12us.common import ROOT,load,save,now
from scripts.stage12c.resources import TERMINAL

def main(launch):
    jobs=load(launch)['jobs'];deadline=time.monotonic()+96*3600
    while time.monotonic()<deadline:
        status=[]
        for j in jobs:
            jid=str(j['slurm_job_id']);path=ROOT/'audit/terminal_receipts'/f'{jid}.json'
            if path.exists():r=load(path)
            else:
                res=subprocess.run(['scontrol','show','job',jid,'-o'],capture_output=True,text=True,check=True)
                r=dict(at=now(),raw=res.stdout,fields=dict(re.findall(r'(\w+)=([^\s]+)',res.stdout)))
                if r['fields'].get('JobState') in TERMINAL:
                    save(path,r);ex=ROOT/'workers'/jid/'exit.json'
                    success=r['fields']['JobState']=='COMPLETED' and r['fields'].get('ExitCode')=='0:0' and ex.exists() and load(ex)['complete']
                    subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','update','--project','.',
                        '--id',j['id'],'--status','succeeded' if success else 'failed','--note','Stage12US finite job terminal; no automatic next action'],check=True)
            status.append((jid,r['fields'].get('JobState')))
        print(now(),status,flush=True)
        if all(s in TERMINAL for _,s in status):
            from scripts.stage12us.review import packets
            packets('science')
            save(ROOT/'audit/generation_collection_complete.json',dict(at=now(),status=status,
                completed_scientific_calls=len([p for p in (ROOT/'generations').glob('*/result.json') if not p.parent.name.startswith('TECH_')]),
                scoring_and_final_analysis_pending=True,next_experiment_launched=False))
            p=Path('reports/stage12us/v1/status.md');p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text('# Stage12U-S execution status\n\nAll six scientific jobs are terminal. Raw outputs, input-integrity checks and continuation-only review packets are preserved. Manual scoring/QC, family analysis, figures and final report remain pending. No next experiment was launched.\n')
            restore_reports_index()
            return
        time.sleep(45)
    save(ROOT/'audit/observer_deadline.json',dict(at=now(),status=status,reason='Finite96-hour receipt-observer deadline; no scientific cancellation or relaunch.'))

def restore_reports_index():
    p=Path('reports/index.md');text=p.read_text();old=(ROOT/'audit/reports_index_before.md').read_text()
    if '## Recent research reports' not in text:
        section=old.split('## Recent research reports',1)[1].split('## GPU Jobs',1)[0]
        text=text.replace('## GPU Jobs','## Recent research reports'+section+'## GPU Jobs',1)
    link='- [Stage12U-S execution status](stage12us/v1/status.md)'
    if link not in text:text=text.replace('## Recent research reports','## Recent research reports\n\n'+link,1)
    p.write_text(text)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('launch');a=p.parse_args();main(a.launch)
