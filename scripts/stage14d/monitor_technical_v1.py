"""Read-only Slurm/receipt status plus terminal snapshots before Slurm purges them."""
import json
import subprocess
import re
from scripts.stage14d.prepare_technical_v1 import ROOT,save


def run():
    states=[]
    for p in sorted((ROOT/'audit/technical_launches_v2').glob('job_*.json')):
        launch=json.loads(p.read_text());jid=launch['job_id']
        final=ROOT/'audit/technical_final_slurm_v2'/f'job_{jid}.json'
        if final.exists():raw=json.loads(final.read_text())['scontrol']
        else:raw=subprocess.run(['scontrol','show','job',jid,'-o'],text=True,capture_output=True,check=True).stdout
        fields=dict(re.findall(r'(\w+)=(\S+)',raw))
        states.append(dict(job=jid,model=launch['model'],state=fields['JobState'],node=fields['NodeList'],runtime=fields['RunTime']))
        if fields['JobState'] in {'COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY'} and not final.exists():
            save(final,dict(job_id=jid,scontrol=raw))
    print(json.dumps(dict(jobs=states,
        admitted=len(list((ROOT/'audit/technical_admissions_v1').glob('*.json'))),
        completed=len(list((ROOT/'raw/technical_v1').glob('*/generation.json'))),
        checked=len(list((ROOT/'raw/technical_v1').glob('*/result.json'))),
        held=(ROOT/'audit/TECHNICAL_HOLD_v2.json').exists()),indent=2))


if __name__=='__main__':run()
