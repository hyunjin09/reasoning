"""CPU-only token-boundary packets for long, scoreable Thinking responses."""
import re
from pathlib import Path
from scripts.stage13a.execution import ROOT,load,save,sha,now
from scripts.stage13a.review import blind_guard,tasks,technical

def prepare():
    blind_guard('T_EQ')
    from tokenizers import Tokenizer
    cfg=load(ROOT/'config.json');tokenizer=Tokenizer.from_file(str(Path(cfg['models']['T']['model']['checkpoint'])/'tokenizer.json'))
    for t in tasks('P'):
        if t['arm']!='T_EQ':continue
        tid=t['task_id'];path=ROOT/'generations'/tid/'generation.json';g=load(path)
        if g['tokens']<32768 or not technical(tid)['validity']['TECHNICALLY_VALID']:continue
        packet=ROOT/'audit/token_budget_packets'/f'{tid}.json'
        if packet.exists():continue
        prefix=tokenizer.decode(g['generated_token_ids'][:32767],skip_special_tokens=True)
        save(packet,dict(at=now(),task_id=tid,generation_sha256=sha(path),prefix=prefix,
            token_boundary_exclusive=32768,full_tokens=g['tokens'],committed_outcome=technical(tid)['outcome'],
            scope='Own-response commitment timing only; no correctness or paired output.'))

def record(tid,eligible,reason):
    blind_guard('T_EQ');assert type(eligible) is bool
    p=ROOT/'generations'/tid/'generation.json';assert load(p)['tokens']>=32768
    save(ROOT/'audit/token_budget'/f'{tid}.json',dict(at=now(),task_id=tid,scoreable_before32k=eligible,
        reason=reason,generation_sha256=sha(p),correctness_used=False))

if __name__=='__main__':prepare()
