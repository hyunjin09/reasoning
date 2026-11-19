"""Finite CPU-only G1 inventory. No cohort acceptance or model calls."""
import argparse
import base64
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from PIL import Image
from scipy.fft import dctn

from scripts.stage14c.source_identity import blind_identity, connected_components


def digest(v): return hashlib.sha256(v.encode()).hexdigest()


def write(path, obj):
    with path.open('x') as f: json.dump(obj, f, indent=2, ensure_ascii=False); f.write('\n')


def image_metrics(payload):
    if isinstance(payload, str): payload = base64.b64decode(payload)
    with Image.open(io.BytesIO(payload)) as image:
        rgb=image.convert('RGB')
        h = digest(str(rgb.size) + '|' + hashlib.sha256(rgb.tobytes()).hexdigest())
        small=np.asarray(rgb.convert('L').resize((32,32), Image.Resampling.LANCZOS), dtype=float)
        dct=dctn(small, type=2)[:8,:8]; bits=dct > np.median(dct)
        phash=int(''.join('1' if x else '0' for x in bits.ravel()),2)
        return dict(image_sha256=hashlib.sha256(payload).hexdigest(), decoded_image_hash=h, image_size=list(rgb.size), phash64=f'{phash:016x}')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--inventory',required=True);args=parser.parse_args()
    spec=json.loads(Path(args.inventory).read_text()); out=Path('outputs/stage14c/source');rows=[];cache={}
    for benchmark, path in spec['parquets'].items():
        table=pq.read_table(path)
        for i,r in enumerate(table.to_pylist()):
            if benchmark=='MMStar':
                payload=r.pop('image'); entry=dict(benchmark=benchmark, row_index=i, item_id=f'MMStar:{r["index"]}', question=r['question'], gold=r['answer'], category=r['category'], stratum=r['category']+'|'+r['l2_category'], metadata=r['meta_info'], family_source_key=None)
            else:
                image=r.pop('image');payload=image['bytes'];metadata=json.loads(r['metadata'])
                entry=dict(benchmark=benchmark,row_index=i,item_id=f'BlindTest:{i}',question=r['prompt'],gold=r['groundtruth'],category=r['task'],stratum=r['task'],metadata=metadata,image_filename=image['path'],family_source_key=blind_identity(r['task'],image['path'],metadata))
            rawhash=hashlib.sha256(payload.encode() if isinstance(payload,str) else payload).hexdigest()
            if rawhash not in cache:
                try:cache[rawhash]=image_metrics(payload)
                except Exception as error:cache[rawhash]=dict(source_error=repr(error))
            entry.update(cache[rawhash]);entry['parquet']=path;rows.append(entry)
            if i%500==0: print(benchmark,i,flush=True)
    edges=[];buckets={}
    for r in rows:
        for kind,key in [('source',r.get('family_source_key')),('pixels',r.get('decoded_image_hash'))]:
            if key is not None:
                token=(r['benchmark'],kind,key)
                if token in buckets:edges.append(dict(a=buckets[token],b=r['item_id'],basis=kind))
                else:buckets[token]=r['item_id']
    components=connected_components([r['item_id'] for r in rows],[(e['a'],e['b']) for e in edges]);byid={r['item_id']:r for r in rows}
    anchors=defaultdict(list)
    for r in json.loads(Path('outputs/stage14a/v1/stage14a_mathvision3040_manifest.json').read_text())['rows']:
        if r.get('decoded_image_hash'):anchors[r['decoded_image_hash']].append(r['problem_id'])
    for r in json.loads(Path('outputs/stage14a/v1/audit/cross_benchmark_exact_source_image_check.json').read_text())['rows']:
        anchors[r['decoded_image_hash']].append(r['mathverse_family_id'])
    families=[]
    for members in components:
        rep=min(members,key=lambda x:(digest('stage14c-g0-v1-20261008|representative|'+x),x));r=byid[rep]
        overlaps=sorted({a for m in members for a in anchors.get(byid[m].get('decoded_image_hash'),[])})
        families.append(dict(family_id=r['benchmark']+':'+digest('|'.join(members))[:24],benchmark=r['benchmark'],stratum=r['stratum'],representative=rep,members=members,anchor_exact_matches=overlaps,status='PRELIMINARY_PENDING_ALIAS_REVIEW'))
    mm=[r for r in rows if r['benchmark']=='MMStar' and 'phash64' in r];pairs=[]
    for i,a in enumerate(mm):
        for b in mm[i+1:]:
            if a['decoded_image_hash']==b['decoded_image_hash']:continue
            distance=(int(a['phash64'],16)^int(b['phash64'],16)).bit_count()
            if distance<=4:pairs.append(dict(a=a['item_id'],b=b['item_id'],distance=distance))
    with (out/'source_rows_v1.jsonl').open('x') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    write(out/'source_alias_edges_v1.json',edges);write(out/'preliminary_families_v1.json',families);write(out/'mmstar_phash_candidates_v1.json',pairs)
    summary=dict(at=datetime.now(timezone.utc).isoformat(),rows_by_benchmark=dict(Counter(r['benchmark'] for r in rows)),source_errors=[r['item_id'] for r in rows if 'source_error' in r],preliminary_families=dict(Counter(r['benchmark'] for r in families)),blind_task_families=dict(Counter(byid[r['representative']]['category'] for r in families if r['benchmark']=='BlindTest')),mmstar_phash_pairs=len(pairs),anchor_exact_overlap_families=sum(bool(r['anchor_exact_matches']) for r in families),native_selection_frozen=False,model_calls=0)
    write(out/'source_identity_inventory_v1.json',summary);print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
