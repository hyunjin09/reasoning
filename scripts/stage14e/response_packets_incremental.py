"""Gold-blind review of completed shards; final scoring still waits for complete coverage."""
import argparse
from pathlib import Path
from scripts.stage14e.common import P,load,rows,save,sha,now
from scripts.stage14b.protocol import extract


def main(rank):
    review=P/'annotations/evaluation_source_review_v1.json'
    assert len(load(review)['records'])==96
    registry=load(P/'manifests/final_execution_registry_v1.json')
    root=Path(registry['solver_roots'][rank]);assert load(root/'result.json')['status']=='COMPLETED'
    logical=load(root/'solver_execution_manifest.json')['rows']
    options={r['item_id']:r['options'] for r in rows('outputs/stage14b/manifests/mathvision_3040_eval_manifest.jsonl')}
    physical={}
    for r in logical:
        path=r['generation_path']
        if path in physical:continue
        g=load(path);assert sha(path)==load(Path(path).with_name('result.json'))['generation_sha256']
        parsed=extract(g['raw_decoded_response'],options[r['item_id']],'T',g['finish_reason'])
        physical[path]=dict(item_id=r['item_id'],generation_path=path,generation_sha256=sha(path),parser=parsed,
            final_body=g['raw_decoded_response'].rsplit('</think>',1)[-1] if '</think>' in g['raw_decoded_response'] else None,
            cap_hit=g['cap_hit'],finish_reason=g['finish_reason'],tokens=g['tokens'],options=options[r['item_id']])
    out=P/f'analysis/response_packet_rank{rank}_v1.json'
    save(out,dict(at=now(),records=list(physical.values()),logical_rows=logical,acquisition_review_sha256=sha(review),gold_used=False))
    with (P/f'analysis/response_packet_rank{rank}_v1.txt').open('x') as f:
        for path,r in physical.items():
            f.write('\n\n'+path+'\nPARSER '+str(r['parser'])+'\nOPTIONS '+str(r['options'])+'\nFINAL\n'+(r['final_body'] if r['final_body'] is not None else 'NO COMMITTED FINAL')+'\n')
    print('Physical records',len(physical))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('rank',type=int,choices=range(4));main(p.parse_args().rank)
