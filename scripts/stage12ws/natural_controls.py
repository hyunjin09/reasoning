"""Prospective matching for the two natural-prefix deletion contrasts, before F."""
from pathlib import Path
from scripts.stage12ws.common import ROOT,load,save,sha,now
from scripts.stage12ws.advance import families
from scripts.stage12ws.controls import closest

def main():
    assert not (ROOT/'audit/phaseF_execution.json').exists(), 'Freeze before any F replay'
    assert load(ROOT/'audit/phaseE_scoring_closed.json')['pass_all']
    f=next(f for f in families() if f['item_id']=='750')
    c=next(c for c in load(ROOT/'audit/candidate_support_freeze.json')['families'] if c['item_id']=='750')
    steps=[s for s in load('outputs/stage12vs/v1/stage12vs_semantic_steps.json')['rows'] if s['item_id']=='750']
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(load(ROOT/'config.json')['arms']['I']['model']['checkpoint'],local_files_only=True)
    rows=[]
    for name,start,end in [('F1_INTERFERE',300,448),('F4_REPAIR',449,598)]:
        raw=''.join(s['text'] for s in steps[:end]);span=''.join(s['text'] for s in steps[start-1:end]);n=len(tok.encode(span,add_special_tokens=False))
        allowed=[b['block_id'] for b in f['blocks'] if b['end_step']<=end and b['block_id'] in c.get('low_importance',[])]
        ids=closest(f['blocks'],allowed,n)
        row=dict(item_id='750',target_condition=name,target_span=[start,end],target_tokens=n,control_removed=ids,
                 baseline=f'P{end}',condition='CTRL_'+name,natural=True)
        if ids is None:rows.append(dict(row,status='NO_ELIGIBLE_CONTROL'));continue
        excluded={k for b in f['blocks'] if b['block_id'] in ids for k in range(b['start_step'],b['end_step']+1)}
        text=''.join(s['text'] for s in steps[:end] if s['step_index'] not in excluded)
        p=ROOT/'prefixes'/f'750_CTRL_{name}.txt'
        with p.open('x') as w:w.write(text)
        cn=sum(b['token_count'] for b in f['blocks'] if b['block_id'] in ids)
        rows.append(dict(row,status='FROZEN',control_tokens=cn,length_ratio=cn/n,adequate_length_match=.8<=cn/n<=1.25,
                    material=dict(prefix_path=str(p),prefix_sha256=sha(p),prefix_tokens=len(tok.encode(text,add_special_tokens=False)),question=f['question'])))
    save(ROOT/'audit/natural_controls_freeze.json',dict(at=now(),rows=rows,no_F_generation=True,
         rationale='Plan section19 includes natural-prefix deletions. Control identities fixed before F; execute only the corresponding high-impact contrast. No block/seed/condition/gate change.'))
    print(rows)

if __name__=='__main__':main()
