"""Answer-safe source review and frozen image-free transfer construction."""
import re
from pathlib import Path
from scripts.stage12xs.execution_v2 import ROOT,load,save,sha,now,CAPS
from scripts.stage12xs.protocol import seed
from scripts.stage12xs.phase_v2 import seal_execution
from scripts.stage12us.protocol import canonical


def source_packets():
    m=load(ROOT/'stage12xs_transfer_candidate_manifest.json');assert len(m['selected_ids'])>=3
    for r in m['rows']:
        path=ROOT/'generations'/f"T_{r['item_id']}_xs1"/'generation.json';g=load(path)
        save(ROOT/'audit/source_packets'/f"T_{r['item_id']}.json",dict(at=now(),item_id=r['item_id'],family_id=r['family_id'],
            question=r['question'],facts=r['facts'],gold=r['answer'],raw=g['raw_decoded_response'],generation_path=str(path),generation_sha256=sha(path)))

def show(item,start=0,end=None,scan=False):
    p=load(ROOT/'audit/source_packets'/f'T_{item}.json');raw=p['raw'];print('ITEM',item,'QUESTION',p['question'])
    if scan:
        for m in re.finditer(r'(?i)answer|\\boxed|(?:total|perimeter|volume|minimum|smallest|condition)[^\n]{0,90}',raw):
            print(m.start(),raw[max(0,m.start()-100):m.end()+180])
    else:print(raw[start:end])

def record(item,cut_marker,evidence_state,reason,quotes,occurrence=0):
    p=load(ROOT/'audit/source_packets'/f'T_{item}.json');raw=p['raw'];positions=[m.start() for m in re.finditer(re.escape(cut_marker),raw)]
    assert len(positions)>occurrence;cut=positions[occurrence];prefix=canonical(raw[:cut])
    assert (quotes or not prefix.strip()) and all(q in prefix for q in quotes)
    assert not re.search(r'\\(?:boxed|fbox)\s*\{|Final\s+Answer\s*:',prefix,re.I)
    assert evidence_state in ['E_FULL','E_PARTIAL','E_WRONG_OR_CONFLICTING','E_UNCLEAR']
    path=ROOT/'prefixes'/f'T_{item}.txt';path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:f.write(prefix)
    save(ROOT/'audit/prefix_reviews'/f'{item}.json',dict(at=now(),item_id=item,family_id=p['family_id'],prefix_path=str(path),prefix_sha256=sha(path),
        raw_cut_offset=cut,cut_marker=cut_marker,occurrence=occurrence,first_excluded_candidate=raw[cut:cut+500],empty_prefix=not bool(prefix.strip()),
        evidence_state=evidence_state,reason=reason,quotes=quotes,canonical_text=prefix,
        EXPLICIT_FINAL_PRESENT=False,ANSWER_CANDIDATE_PRESENT=False,
        GOLD_VALUE_INCIDENTALLY_PRESENT=bool(re.search(r'(?<!\w)'+re.escape(str(p['gold']))+r'(?!\w)',prefix)),
        generation_path=p['generation_path'],generation_sha256=p['generation_sha256'],transfer_outcomes_inspected=False,
        review='Source-only semantic first-candidate review; same agent, not independent annotation. Incidental gold uses exact string occurrence only.'))

def freeze():
    m=load(ROOT/'stage12xs_transfer_candidate_manifest.json');ids=m['selected_ids'];assert 3<=len(ids)<=10
    rows=[load(ROOT/'audit/prefix_reviews'/f'{i}.json') for i in ids]
    # CPU tokenizer verification only; never loads CUDA weights.
    from transformers import AutoProcessor
    from scripts.stage12us.protocol import render
    cfg=load(ROOT/'config.json');processors={k:AutoProcessor.from_pretrained(v['model']['checkpoint'],local_files_only=True) for k,v in cfg['models'].items()}
    index={r['item_id']:r for r in rows};partners={i:ids[(k+1)%len(ids)] for k,i in enumerate(ids)};tasks=[];lengths=[]
    for r in m['rows']:
        for condition in ['RT_T','RT_I','Q_I','Q_T','SH_I']:
            key=condition[-1];source=partners[r['item_id']] if condition=='SH_I' else r['item_id'] if condition.startswith('RT') else None
            prefix=index[source]['canonical_text'] if source else ''
            rendered=render(processors[key],r['question'],prefix,key)
            ntokens=len(rendered['prompt_token_ids']);assert ntokens+CAPS[condition]<cfg['runtime']['max_model_len'],(r['item_id'],condition,ntokens)
            lengths.append(dict(item_id=r['item_id'],condition=condition,prompt_tokens=ntokens,prefix_tokens=len(processors[key].tokenizer.encode(prefix,add_special_tokens=False))))
            for replicate in range(5):
                tasks.append(dict(task_id=f"{condition}_{r['item_id']}_r{replicate}",item_id=r['item_id'],family_id=r['family_id'],arm=condition,model_key=key,
                    replicate=replicate,cap=CAPS[condition],prompt=r['question'],prefix=prefix,prompt_version='stage12xs-answer-safe-v2',
                    image=None,image_sha256=None,source_item_id=source,source_family_id=index[source]['family_id'] if source else None,
                    prefix_path=index[source]['prefix_path'] if source else None,prefix_sha256=index[source]['prefix_sha256'] if source else None,
                    seed=seed(r['family_id'],condition,replicate)))
    save(ROOT/'stage12xs_answer_safe_prefixes.json',dict(at=now(),frozen=True,rows=rows,token_lengths=lengths,shuffle_partners=partners,
        canonicalization='Only think control wrappers removed; all whitespace retained',transfer_outcomes_inspected=False))
    shards=[]
    for key in ['I','T']:
        own=[t for t in tasks if t['model_key']==key]
        for k in range(2):shards.append((key,own[k::2]))
    paths=seal_execution('C',m['rows'],tasks,shards)
    save(ROOT/'audit/prefix_seal.json',dict(at=now(),files={str(p):sha(p) for p in [ROOT/'stage12xs_answer_safe_prefixes.json',ROOT/'audit/phaseC_execution.json',*[Path(r['prefix_path']) for r in rows]]},target_generation_started=False))
    print('PhaseC frozen',len(tasks),'calls',paths)
