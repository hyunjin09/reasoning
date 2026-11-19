"""Freeze human/agent-authored critical-step edits; never generate or score them."""
from pathlib import Path
from transformers import AutoProcessor
from scripts.stage12vs.common import ROOT,load,save,sha,now
from scripts.stage12vs.protocol import seed,render
from scripts.stage12vs.advance import families,freeze_wave


def main():
    assert load(ROOT/'audit/replication_gate.json')['continue']
    local=load(ROOT/'stage12vs_fine_localization.json')['families']
    stable={r['item_id']:r for r in local if r['status']=='STABLE'}
    edits=load(ROOT/'audit/manual_intervention_edits.json')['rows']
    assert {r['item_id'] for r in edits}==set(stable)
    steps=load(ROOT/'stage12vs_semantic_steps.json')['rows'];annotations=load(ROOT/'stage12vs_step_annotations.json')['rows']
    old_oracles={r['item_id']:r for r in load('outputs/stage12b/v1/stage12b_oracle_prompts.json')['rows']}
    cfg=load(ROOT/'config.json');proc=AutoProcessor.from_pretrained(cfg['arms']['I']['model']['checkpoint'])
    audit=[];content=[];optional=[]
    for edit in edits:
        item=edit['item_id'];loc=stable[item];k=loc['b'];f=next(x for x in families() if x['item_id']==item)
        ss=[s for s in steps if s['item_id']==item];an={r['step_index']:r for r in annotations if r['item_id']==item}
        step=ss[k-1];before=''.join(s['text'] for s in ss[:k-1]);after=before+step['text']
        assert edit['step_index']==k and edit['original_step']==step['text']
        assert edit['answer_candidate_inserted'] is False and edit['paraphrase_preserves_proposition'] is True
        assert edit['cf_changes_one_semantic_conclusion'] is True
        eligible=[s for s in ss[:k-1] if (an[s['step_index']]['category']=='META_REASONING' or an[s['step_index']]['restates_prior_content'])
                  and an[s['step_index']]['introduces_new_factual_proposition'] is not True
                  and not an[s['step_index']]['introduces_new_numeric_symbolic_value']]
        assert eligible,('No identifiable matched noncritical control; preserve as non-identifiable, do not invent',item)
        target_tokens=len(proc.tokenizer.encode(step['text'],add_special_tokens=False))
        ctrl=min(eligible,key=lambda s:(abs(len(proc.tokenizer.encode(s['text'],add_special_tokens=False))-target_tokens),s['step_index']))
        assert edit['control_step_index']==ctrl['step_index'] and edit['control_has_no_new_proposition_or_value'] is True
        cf=edit['counterfactual_text'];para=edit['paraphrase_text']
        assert cf!=step['text'] and para!=step['text']
        assert .5<=len(cf)/max(1,len(step['text']))<=2 and .5<=len(para)/max(1,len(step['text']))<=2
        drop_ctrl=after[:ctrl['start']]+after[ctrl['end']:]
        conditions=[('C1_DROP',f['question'],before),('C2_CF',f['question'],before+cf),
                    ('C3_PARA',f['question'],before+para),('C4_CTRL_DROP',f['question'],drop_ctrl),
                    ('C5_ESTAR',old_oracles[item]['prompt'],''),('E_PLUS_STEP',old_oracles[item]['prompt'],step['text'])]
        assert old_oracles[item]['image'] is None and f['question'] in old_oracles[item]['prompt']
        for condition,question,text in conditions:
            p=ROOT/'prefixes'/f'{condition}_{item}.txt'
            with p.open('x') as h:h.write(text)
            inp=render(proc,question,text,'I');assert len(inp['prompt_token_ids'])+32768<=128000
            for rep in range(3):
                phase='optionalE' if condition=='E_PLUS_STEP' else 'contentC'
                task=dict(task_id=f'{condition}_{item}_k{k}_r{rep}',phase=phase,condition=condition,cohort='primary',
                    item_id=item,family_id=f['family_id'],original_question=f['question'],question=question,target='I',step_index=k,
                    replicate=rep,seed=seed(f['family_id'],condition,k,rep),prefix_path=str(p),prefix_sha256=sha(p))
                (optional if phase=='optionalE' else content).append(task)
        audit.append(dict(**edit,critical_source_category=an[k]['category'],critical_source_annotation=an[k],
            matched_control=ctrl,target_step_tokens=target_tokens,
            control_step_tokens=len(proc.tokenizer.encode(ctrl['text'],add_special_tokens=False)),
            drop_equals_before=True,original_oracle_prompt=old_oracles[item]['prompt']))
    save(ROOT/'stage12vs_critical_step_interventions.json',dict(at=now(),rows=audit,
        manual_edits_sha256=sha(ROOT/'audit/manual_intervention_edits.json'),all_texts_frozen_before_intervention_generation=True))
    freeze_wave('contentC',content,shards=min(2,len(stable)))
    freeze_wave('optionalE',optional)
    print('Frozen content',len(content),'optional',len(optional),'calls; optional execution remains budget-gated')


if __name__=='__main__':main()
