from pathlib import Path
from scripts.stage14d1.common import load,save,sha,now,rows
P=Path('outputs/stage14e_acquisition_development/v1')


def update(path,value):
    """Mutable operational snapshot, with immutable prior versions retained."""
    import os,time,json
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        history=path.parent/'snapshot_history';history.mkdir(exist_ok=True)
        prior=history/(path.stem+'_'+str(time.time_ns())+'.json')
        prior.write_bytes(path.read_bytes())
    temp=path.with_name(path.name+'.'+str(os.getpid())+'.update')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    os.replace(temp,path)
