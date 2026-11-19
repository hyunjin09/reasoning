"""First successful equal-evidence source; maximal pre-answer text, no image."""
import re
from pathlib import Path
from scripts.stage12ys.execution import ROOT,load,save,sha,now,cohort,task,CAPS
from scripts.stage12ys.phases import seal_execution
from scripts.stage12us.protocol import canonical,render

def source_packets():
    m=load(ROOT/'stage12ys_phaseC_candidate_manifest.json');assert m['n_selected']>=2
    by={r['item_id']:r for r in cohort()}
    for r in m['rows']:
        p=Path(r['source_generation']);assert sha(p)==r['source_generation_sha256'];g=load(p);row=by[r['item_id']]
        assert g['arm']=='T_E' and g['visual_tokens']==0 and g['replicate']==r['source_replicate']
        dest=ROOT/'audit/source_packets'/f"T_{r['item_id']}.json"
        if not dest.exists():save(dest,dict(at=now(),item_id=r['item_id'],family_id=r['family_id'],question=row['question'],oracle=row['prompts']['O'],
            facts=row['facts'],gold=row['answer'],raw=g['raw_decoded_response'],generation_path=str(p),generation_sha256=sha(p),source_replicate=r['source_replicate']))

def show(item,start=0,end=None,scan=False):
    p=load(ROOT/'audit/source_packets'/f'T_{item}.json');raw=p['raw'];print('ITEM',item,'QUESTION',p['question'])
    if scan:
        for m in re.finditer(r'(?i)answer|\\boxed|(?:total|perimeter|volume|minimum|smallest|condition)[^\n]{0,90}',raw):print(m.start(),raw[max(0,m.start()-100):m.end()+180])
    else:print(raw[start:end])

def record(item,cut_marker,reason,quotes,incidental_gold=None,occurrence=0):
    p=load(ROOT/'audit/source_packets'/f'T_{item}.json');raw=p['raw'];positions=[m.start() for m in re.finditer(re.escape(cut_marker),raw)]
    assert len(positions)>occurrence;cut=positions[occurrence];prefix=canonical(raw[:cut])
    assert (quotes or not prefix.strip()) and all(q in prefix for q in quotes)
    assert not re.search(r'\\(?:boxed|fbox)\s*\{|Final\s+Answer\s*:',prefix,re.I)
    path=ROOT/'prefixes'/f'T_E_{item}.txt';path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:f.write(prefix)
    exact=bool(re.search(r'(?<!\w)'+re.escape(str(p['gold']))+r'(?!\w)',prefix))
    save(ROOT/'audit/prefix_reviews'/f'{item}.json',dict(at=now(),item_id=item,family_id=p['family_id'],prefix_path=str(path),prefix_sha256=sha(path),
        raw_cut_offset=cut,cut_marker=cut_marker,occurrence=occurrence,first_excluded_candidate=raw[cut:cut+500],empty_prefix=not bool(prefix.strip()),
        reason=reason,quotes=quotes,canonical_text=prefix,EXPLICIT_FINAL_PRESENT=False,ANSWER_CANDIDATE_PRESENT=False,
        GOLD_VALUE_INCIDENTALLY_PRESENT=exact if incidental_gold is None else incidental_gold,exact_gold_string_present=exact,
        generation_path=p['generation_path'],generation_sha256=p['generation_sha256'],source_replicate=p['source_replicate'],
        transfer_outcomes_inspected=False,review='Source-only full-prefix semantic review; same agent, not independent annotation.'))

def freeze():
    m=load(ROOT/'stage12ys_phaseC_candidate_manifest.json');ids=m['selected_ids'];assert 2<=len(ids)<=10
    rows=[load(ROOT/'audit/prefix_reviews'/f'{i}.json') for i in ids];index={r['item_id']:r for r in rows}
    from transformers import AutoProcessor
    cfg=load(ROOT/'config.json');procs={k:AutoProcessor.from_pretrained(v['model']['checkpoint'],local_files_only=True) for k,v in cfg['models'].items()}
    by={r['item_id']:r for r in cohort()};partners={i:ids[(k+1)%len(ids)] for k,i in enumerate(ids)};new=[];lengths=[]
    for i in ids:
        for a in ['RT_T','RT_I','Q_I','SH_I']:
            key='T' if a=='RT_T' else 'I';source=partners[i] if a=='SH_I' else i if a.startswith('RT') else None
            prefix=index[source]['canonical_text'] if source else ''
            rendered=render(procs[key],by[i]['prompts']['O'],prefix,key);nt=len(rendered['prompt_token_ids'])
            assert nt+CAPS[a]<cfg['runtime']['max_model_len'],('Do not truncate frozen prefix or cap',i,a,nt)
            lengths.append(dict(item_id=i,arm=a,prompt_tokens=nt,prefix_tokens=len(procs[key].tokenizer.encode(prefix,add_special_tokens=False))))
            for k in range(5):
                t=task(by[i],a,'C',k);t.update(prefix=prefix,source_item_id=source,source_family_id=index[source]['family_id'] if source else None,
                    prefix_path=index[source]['prefix_path'] if source else None,prefix_sha256=index[source]['prefix_sha256'] if source else None)
                new.append(t)
    p=ROOT/'stage12ys_phaseC_answer_safe_prefixes.json'
    save(p,dict(at=now(),frozen=True,rows=rows,token_lengths=lengths,shuffle_partners=partners,source_input='Frozen Q+E* text only',
        canonicalization='Only think wrappers removed; whitespace retained',target_outcomes_inspected=False))
    paths=seal_execution('C',new,p,2)
    save(ROOT/'audit/prefix_seal.json',dict(at=now(),files={str(p):sha(p) for p in [p,ROOT/'audit/phaseC_execution.json',*[Path(r['prefix_path']) for r in rows]]},target_generation_started=False,manifests=paths))
    print('C sealed',len(new),'calls',paths)
