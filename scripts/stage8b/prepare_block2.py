"""Freeze exact Block0 membership and build packets without labels or feature values."""
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from visual_reasoning.stage8b.block1_data import digest,save

ROOT=Path('outputs/stage8b_block2/v1')
B0=Path('outputs/stage8b_block0/v1')


def main():
    freezes=[B0/'stage8b_block0_freeze.json',Path('outputs/stage8b_block1/v1/stage8b_block1_freeze.json')]
    verified={}
    for path in freezes:
        obj=json.loads(path.read_text())
        for p,h in {**obj['artifacts_sha256'],**obj['supporting_sha256']}.items():
            assert digest(p)==h,p
        verified[str(path)]=digest(path)
    membership_path=B0/'stage8b_block0_review_membership.json'
    members=json.loads(membership_path.read_text())['rows']
    cohort=json.loads((B0/'stage8b_block0_cohort_manifest.json').read_text())['rows']
    manifest={r['item_id']:r for r in map(json.loads,Path('outputs/stage8b1a/cohort/census256_manifest_v1.jsonl').read_text().splitlines())}
    events=pd.read_parquet(B0/'stage8b_block0_retrieval_episode_table.parquet',columns=['event_id','item_id','episode_index','start_token','end_token'])
    events=events.set_index('event_id');ids=[e for row in members for e in row['event_ids']]
    assert len(ids)==len(set(ids))==456 and len(members)==len(cohort)==256
    native_paths={};packets=[];sources={};counts={};review_order=0
    for member,source in zip(members,cohort):
        item=member['item_id'];assert item==source['item_id']
        row=manifest[item];image=Path(row['image']).resolve()
        assert image.is_relative_to(Path('/data/dataset')) and digest(image)==row['image_sha256']
        native=Path(source['receipt']).parent
        native_paths[item]=str(native)
        receipt=json.loads((native/'result.json').read_text());assert digest(native/'result.json')==source['receipt_sha256']
        counts[item]=len(member['event_ids'])
        if not member['event_ids']:continue
        tokens=[json.loads(s) for s in (native/'tokens.jsonl').read_text().splitlines()]
        assert digest(native/'tokens.jsonl')==receipt['provenance_sha256'][str(native/'tokens.jsonl')]
        pieces=[t['decoded_token'] for t in tokens];text=''.join(pieces)
        from visual_reasoning.stage8b.transfer import reasoning_length
        length=reasoning_length(pieces);pieces=pieces[:length]
        safe=dict(item_id=item,family_id=row['family_id'],order=row['order'],image=str(image),image_sha256=row['image_sha256'],image_size=row['image_size'],question=row['question'],subject=row['subject'],reasoning_tokens=length,token_file=str(native/'tokens.jsonl'),token_sha256=digest(native/'tokens.jsonl'),events=[])
        lines=[f'# MathVision {item} — selected episodes\n',row['question']+'\n',f'Image: {image}\n']
        for eid in member['event_ids']:
            e=events.loc[eid];start,end=int(e.start_token),int(e.end_token)
            a,b=max(0,start-256),min(length,end+193)
            local=dict(event_id=eid,review_order=review_order,episode_index=int(e.episode_index),start_token=start,end_token=end,context_start=a,context_end=b,association_start=max(0,start-16),association_end=min(length,end+129))
            safe['events'].append(local);packets.append(dict(item_id=item,**local));review_order+=1
            lines.append(f'## {eid} [{start}:{end+1}] context[{a}:{b}]\n')
            boundaries=sorted(set([a,start,end+1,b]+list(range(a,b,64))))
            for l,h in zip(boundaries,boundaries[1:]):
                if l<h:lines.append(f'[{l}:{h}] '+''.join(pieces[l:h])+'\n')
        dest=ROOT/'annotations'/'packets'/item
        save(dest.with_suffix('.json'),safe)
        dest.with_suffix('.md').write_text('\n'.join(lines))
        sources[str(dest.with_suffix('.json'))]=digest(dest.with_suffix('.json'))
        sources[str(dest.with_suffix('.md'))]=digest(dest.with_suffix('.md'))
    assert len(packets)==456
    save(ROOT/'audit'/'preparation_freeze.json',dict(at=datetime.now(timezone.utc).isoformat(),input_freezes=verified,membership_path=str(membership_path),membership_sha256=digest(membership_path),protocol_sha256=digest('plan/stage8b_block2_execution_protocol_v1.md'),plan_sha256=digest('plan/stage8b_block2_retrieval_event_local_read_success_failure_plan.md'),preparer_sha256=digest(__file__),examples=256,review_events=456,review_families=sum(n>0 for n in counts.values()),selected_counts=counts,native_paths=native_paths,events=packets,packet_sha256=sources,packet_omissions=['benchmark label','ground truth answer','feature values'],annotation_complete=False))
    print(json.dumps(dict(events=456,families=sum(n>0 for n in counts.values()),no_selected_events=sum(n==0 for n in counts.values()))))


if __name__=='__main__':main()
