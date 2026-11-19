"""Seal both technical workers; no experiment may consume partial checks."""
import json
from datetime import datetime, timezone
from pathlib import Path
from scripts.stage8c.prepare import save, sha, ROOT


def main():
    rows=[]
    for rank in range(2):
        p=ROOT/'technical_v2'/f'worker{rank}'/'result.json'
        r=json.loads(p.read_text());assert r['pass_checks']
        assert len(r['results'])==2
        for item in r['results']:
            assert set(item['checks'])=={'V1','V2','V3','V4','V5','V6'}
            assert all(c['pass_check'] for c in item['checks'].values())
        rows.append(dict(path=str(p),sha256=sha(p),items=[x['item_id'] for x in r['results']]))
    save(ROOT/'stage8c_v2_technical_validation.json',dict(at=datetime.now(timezone.utc).isoformat(),
         pass_checks=True,workers=rows,config_sha256=sha(ROOT/'audit/technical_config_v2.json')))
    print('All V1–V6 checks passed on both allocated GPUs.',flush=True)


if __name__=='__main__':main()
