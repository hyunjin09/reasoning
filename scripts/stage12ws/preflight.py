"""CPU-only checks before any generation."""
import ast
from pathlib import Path
from scripts.stage12ws.common import ROOT,load,save,sha,now
from scripts.stage12ws.protocol import authorize,render,seed
from transformers import AutoProcessor

def main():
    assert not list((ROOT/'generations').glob('*/generation.json'))
    cfg=load(ROOT/'config.json');proc=AutoProcessor.from_pretrained(cfg['arms']['I']['model']['checkpoint'],local_files_only=True)
    for p in Path('scripts/stage12ws').glob('*.py'):ast.parse(p.read_text())
    m=load(ROOT/'stage12ws_primary_manifest.json');ss=load('outputs/stage12vs/v1/stage12vs_semantic_steps.json')['rows'];checks=[]
    for f in m['families']:
        source=Path(f['source_prefix_path']).read_text()
        assert ''.join(Path(b['path']).read_text() for b in f['blocks'])==source
        assert Path(f['conditions']['FULL']['prefix_path']).read_text()==source
        for cond,c in f['conditions'].items():
            text=Path(c['prefix_path']).read_text();assert sha(c['prefix_path'])==c['prefix_sha256']
            inp=render(proc,c['question'],text,'I');assert len(inp['prompt_token_ids'])+32768<=128000
            checks.append(dict(item_id=f['item_id'],condition=cond,prompt_tokens=len(inp['prompt_token_ids']),image_present=inp['image_present']))
        assert len({seed(f['family_id'],i) for i in range(7)})==7
    for p in (ROOT/'queues').glob('phaseA_*.json'):authorize(load(p))
    assert len(load(ROOT/'audit/phaseA_execution.json')['tasks'])==56
    assert all(sha(p)==h for p,h in load(ROOT/'audit/source_seal.json')['hashes'].items())
    save(ROOT/'audit/preflight.json',dict(at=now(),pass_all=True,checks=checks,phaseA_calls=56,prior_files=6709,no_generation=True,
         analysis_hashes={str(p):sha(p) for p in Path('scripts/stage12ws').glob('*.py')}))
    print('PREFLIGHT PASS',len(checks),'conditions,max prompt',max(c['prompt_tokens'] for c in checks))

if __name__=='__main__':main()
