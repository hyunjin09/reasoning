"""Freeze every eligible native trace; export only semantic input for reviewers."""
import os,re,bisect,json
from collections import Counter
from pathlib import Path
from scripts.stage10b.common import ROOT,PROTOCOL,load,save,sha,now
from scripts.stage10b.protocol import paragraphs

CUE=re.compile(r'\b(?:figure|diagram|image|graph|table|picture|plot|drawing|visually|shown|looking|look|observe|notice|see|check|read|identify|locate|count|shaded|label(?:ed|s)?|marked)\b|(?:图中|如图|图像|图形|观察|看图|示意图|标注)',re.I)


def main():
    assert os.environ.get('SLURM_JOB_ID')
    vpath=Path('outputs/stage9a/v1/stage9a_cohort_manifest.json');mpath=Path('outputs/stage8a/cohort/main_manifest_v1.jsonl')
    vision=load(vpath)['rows'];verse=[json.loads(s) for s in mpath.read_text().splitlines() if s.strip()]
    verse_paths={p.parent.name:p.parent for p in Path('outputs/stage8a/native/main_v1').glob('worker*/examples/*/generation.json')}
    rows=[];images={}
    for dataset,items in [('MathVision',vision),('MathVerse',verse)]:
        for item in items:
            ident=str(item['item_id'] if dataset=='MathVision' else item['base_id'])
            tid=f'{dataset.lower()}_{ident}';d=Path(f'outputs/stage9a/v1/native/examples/thinking_{ident}') if dataset=='MathVision' else verse_paths[ident]
            files={name:d/name for name in ('generation.json','tokens.jsonl','result.json','input.json','manifest_row.json')}
            assert all(p.exists() for p in files.values())
            g=load(files['generation.json']);inp=load(files['input.json']);tokens=[json.loads(s) for s in files['tokens.jsonl'].read_text().splitlines()]
            assert len(tokens)==g['tokens'] and [t['token_id'] for t in tokens]==g['generated_token_ids']
            if dataset=='MathVision':span=g['reasoning_span'];start,end=span['start'],span['end']
            else:
                start=0;end=next((i for i,t in enumerate(tokens) if t['token_id']==151668),len(tokens))
            pieces=[t['decoded_token'] for t in tokens];offsets=[0]
            for t in pieces:offsets.append(offsets[-1]+len(t))
            text=''.join(pieces);reason=text[offsets[start]:offsets[end]];para=[]
            for part in paragraphs(reason):
                lo=offsets[start]+part['start'];hi=offsets[start]+part['end'];s=part['text']
                para.append(dict(index=len(para),char_start=lo,char_end=hi,token_start=bisect.bisect_right(offsets,lo)-1,
                    token_end=bisect.bisect_left(offsets,hi),text=s,visual_cue=bool(CUE.search(s))))
            assert not para or max(p['char_end'] for p in para)<=offsets[end]
            image=Path(item['image']);assert sha(image)==item['image_sha256']
            identity=item.get('decoded_image_sha256',item['image_sha256']);duplicate=images.get(identity);images.setdefault(identity,tid)
            packet=dict(trajectory_id=tid,dataset=dataset,item_id=ident,family_id=item['family_id'],image=str(image),image_sha256=sha(image),
                question=inp['question'],reasoning_start=start,reasoning_end=end,full_reasoning_text=reason,
                token_character_offsets=offsets,reasoning_char_start=offsets[start],paragraphs=para,
                blinding='Question/image/reasoning only; no correctness, detector, routing, gold or causal outcome.',
                index_scope='All paragraphs matching frozen navigation cues; not an exhaustive implicit-demand detector.')
            packet_path=ROOT/f'packets/{tid}.json';save(packet_path,packet)
            full_path=ROOT/f'packets/{tid}.txt';full_path.parent.mkdir(parents=True,exist_ok=True)
            with full_path.open('x') as f:
                f.write(f'{tid}\nQUESTION: {inp["question"]}\nIMAGE: {image}\n\n')
                for p in para:f.write(f'[p{p["index"]} tokens {p["token_start"]}:{p["token_end"]}] {p["text"]}\n\n')
            # All cue paragraphs, deduplicated only by exact text, retain every occurrence.
            groups={}
            for p in para:
                if p['visual_cue']:groups.setdefault(p['text'],[]).append(p)
            index=ROOT/f'packets/{tid}_index.txt'
            with index.open('x') as f:
                f.write(f'{tid}\nQUESTION: {inp["question"]}\nIMAGE: {image}\nFULL: {full_path}\n\n')
                for s,ps in groups.items():
                    p=ps[0];prior=para[p['index']-1]['text'] if p['index'] else ''
                    f.write('OCCURRENCES '+str([(x['index'],x['token_start'],x['token_end']) for x in ps])+'\n')
                    f.write('PREVIOUS: '+prior[-700:]+'\nCUE: '+s+'\n\n')
            rows.append(dict(trajectory_id=tid,dataset=dataset,item_id=ident,family_id=item['family_id'],source_type=item.get('source',item.get('subject','unknown')),
                subject=item.get('subject'),image=str(image),image_sha256=sha(image),decoded_image_sha256=identity,duplicate_of=duplicate,
                eligible=duplicate is None,reasoning_tokens=end-start,generated_tokens=g['tokens'],normal_eos=g['normal_eos'],at_length_cap=g['at_length_cap'],
                model_revision=g['model_revision'],generation_seed=g['seed'],native_directory=str(d),packet_path=str(packet_path),text_path=str(full_path),index_path=str(index),
                source_sha256={str(p):sha(p) for p in files.values()},packet_sha256=sha(packet_path),paragraphs=len(para),cue_paragraphs=sum(p['visual_cue'] for p in para),
                passive_path=str(d/'passive.npz') if (d/'passive.npz').exists() else None))
    assert len(rows)==224 and Counter(r['dataset'] for r in rows)=={'MathVision':128,'MathVerse':96}
    save(ROOT/'stage10b_corpus_manifest.json',dict(at=now(),frozen=True,rows=rows,source_manifests_sha256={str(p):sha(p) for p in (vpath,mpath)},
        protocol_sha256=sha(PROTOCOL),selection='All224 prior main natural native Thinking trajectories; no correctness/length/routing filter.',
        independent_unit='conservative problem/image trajectory',eligible=sum(r['eligible'] for r in rows),
        detector_values_opened=False,new_generations=0))
    with (ROOT/'stage10b_recurrent_demand_census_spec.md').open('x') as f:f.write(PROTOCOL.read_text())
    save(ROOT/'audit/preparation_receipt.json',dict(at=now(),slurm_job_id=os.environ['SLURM_JOB_ID'],
        sources_sha256={str(p):sha(p) for p in Path('scripts/stage10b').glob('*.py')},
        plan_sha256=sha('plan/stage10b_recurrent_visual_demand_census_plan.md'),manifest_sha256=sha(ROOT/'stage10b_corpus_manifest.json')))
    print('FROZEN',len(rows),'eligible',sum(r['eligible'] for r in rows),'reasoning tokens',sum(r['reasoning_tokens'] for r in rows),flush=True)


if __name__=='__main__':main()
