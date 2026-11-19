"""CPU-only own-response outcome timing at the strict32768-token boundary."""
from pathlib import Path
from scripts.stage13b.execution import ROOT,load,save,sha,now
from scripts.stage13b.review import tasks,technical


def prepare():
    from tokenizers import Tokenizer
    cfg=load(ROOT/'config.json');tokenizers={}
    for t in tasks():
        if t['phase']=='technical' or t['mode']!='T':continue
        cell=t['scale']+'_'+t['arm']
        if not (ROOT/'audit/scoring_closed'/f'{cell}.json').exists():continue
        tid=t['task_id'];path=ROOT/'generations'/tid/'generation.json';g=load(path);a=technical(tid)
        if g['tokens']<32768 or not a['validity']['TECHNICALLY_VALID'] or a['outcome']=='__NO_ANSWER__':continue
        target=ROOT/'audit/token_budget_packets'/f'{tid}.json'
        if target.exists():continue
        key=t['model_key']
        if key not in tokenizers:tokenizers[key]=Tokenizer.from_file(str(Path(cfg['models'][key]['model']['checkpoint'])/'tokenizer.json'))
        prefix=tokenizers[key].decode(g['generated_token_ids'][:32767],skip_special_tokens=True)
        save(target,dict(at=now(),task_id=tid,prefix=prefix,full_tokens=g['tokens'],outcome=a['outcome'],
            token_boundary_exclusive=32768,generation_sha256=sha(path),correctness_used=False))


def record(tid,eligible,reason):
    assert type(eligible) is bool
    p=ROOT/'audit/token_budget_packets'/f'{tid}.json';packet=load(p)
    save(ROOT/'audit/token_budget'/f'{tid}.json',dict(at=now(),task_id=tid,scoreable_before32k=eligible,
        reason=reason,generation_sha256=packet['generation_sha256'],packet_sha256=sha(p),correctness_used=False))


if __name__=='__main__':prepare()
