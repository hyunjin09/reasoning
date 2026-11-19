"""Finite source-only approximate overlap screen; matches require manual review."""
import json
from pathlib import Path
from scripts.stage14c.audit_sources import image_metrics, write


def main():
    root=Path('outputs/stage14c/source')
    rows=[json.loads(line) for line in (root/'source_rows_v1.jsonl').read_text().splitlines()]
    # One representative per exact new image, including both proposed tasks.
    unique={r['decoded_image_hash']:r for r in rows}
    new=[(r['item_id'],int(r['phash64'],16)) for r in unique.values()]
    anchor=[]
    for r in json.loads(Path('outputs/stage14a/v1/stage14a_mathvision3040_manifest.json').read_text())['rows']:
        anchor.append((r['problem_id'],r['image']))
    for r in json.loads(Path('outputs/stage14a/v1/audit/cross_benchmark_exact_source_image_check.json').read_text())['rows']:
        anchor.append((r['mathverse_family_id'],r['image']))
    result=[];metrics=[]
    for i,(key,path) in enumerate(anchor):
        p=Path(path).resolve()
        if not (p.is_relative_to(Path('/data/dataset')) or p.is_relative_to(Path.cwd())):raise ValueError('Path outside access roots')
        m=image_metrics(p.read_bytes());h=int(m['phash64'],16);metrics.append(dict(anchor_id=key,path=path,**m))
        for item_id,other in new:
            distance=(h^other).bit_count()
            if distance<=4:result.append(dict(anchor_id=key,anchor_image=path,new_item_id=item_id,distance=distance))
        if i%500==0:print('anchor',i,flush=True)
    write(root/'anchor_source_image_metrics_v1.json',metrics)
    write(root/'anchor_phash_candidates_v1.json',result)
    print('candidates',len(result),flush=True)


if __name__=='__main__': main()
