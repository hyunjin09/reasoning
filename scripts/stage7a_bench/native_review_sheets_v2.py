"""Render bounded annotated source-review sheets; never cache raw datasets.

For no-image conditions the paired original is an adjudication reference only.
Full prompts and release answers are printed separately, without truncation.
"""
import argparse
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset, payload, describe, user_content

OUT = ROOT / 'outputs/stage7a_bench_v2'


def render(manifest, start, end):
    manifest = (ROOT / manifest).resolve()
    if not manifest.is_relative_to(OUT / 'cohort/benchmark_manifests'):
        raise ValueError('Use an active frozen native manifest')
    rows = read_jsonl(manifest)
    matches = [r for r in read_json(OUT / 'cohort/sample_freeze.json')['native_screen'].values()
               if r['sha256'] == sha(manifest) and r['count'] == len(rows)]
    if len(matches) != 1 or not (0 <= start < end <= len(rows)) or end-start > 6:
        raise ValueError('Use a uniquely frozen manifest and a bounded range of at most six examples')
    dest = OUT / 'native_screen/source_review_sheets'
    dest.mkdir(parents=True, exist_ok=True)
    records = []
    for index in range(start, end):
        row = rows[index]
        if row.get('document_path') or row['benchmark'] == 'phantom_0':
            raise ValueError('Use the separate document-page or Phantom review workflow')
        reference_only = row.get('no_image', False)
        assets = row.get('source_asset_identity', []) if reference_only else row.get('image_assets', [])
        if row.get('image_path') and not reference_only:
            asset = dict(kind='file', path=row['image_path'], slot='image_1')
            data = payload(asset)
            if sha(row['image_path']) != row['image_sha256']:
                raise ValueError('Native image file hash changed')
            assets = [describe(asset, data)]
        images = [(a['slot'], load_asset(a)) for a in assets]
        if not images:
            raise ValueError('No source image to review')
        if reference_only:
            order = [slot for slot, _ in images]
        else:
            _, order = user_content(row, images)
        lookup = dict(images)
        panels = [(slot, lookup[slot]) for slot in order]
        paths = []
        scope = 'REFERENCE ONLY — model received no image' if reference_only else 'FROZEN NATIVE INPUT'
        for offset in range(0, len(panels), 3):
            chunk = panels[offset:offset+3]
            fig, axes = plt.subplots(1, len(chunk), figsize=(16,9), dpi=120, squeeze=False)
            for ax, (slot, im) in zip(axes.flat, chunk):
                ax.imshow(im)
                ax.set_title(f'{slot} | {im.width} × {im.height} native pixels', fontsize=11)
                ax.set_axis_off()
            fig.suptitle(f"{index:03d} {row['benchmark']} | {row['example_id']}\n{row['condition']} | {scope}", fontsize=12)
            fig.text(.02,.02,'Annotated review display; native image pixels and prompt remain unchanged. Enlarge the source before judging small glyphs.',fontsize=9)
            fig.subplots_adjust(top=.87,bottom=.07,wspace=.05)
            path = dest / f"{row['event_id']}__part{offset//3}.png"
            fig.savefig(path)
            plt.close(fig)
            paths.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
        for _, im in images: im.close()
        record = dict(index=index,event_id=row['event_id'],manifest_sha256=sha(manifest),
            prompt=row['prompt'],release_answer=row.get('answer'),
            release_answer_status='Not independently adjudicated by rendering',
            reference_only=reference_only,source_assets=assets,display_order=order,
            files=paths,native_outputs_read=False,causal_scores_read=False,
            renderer_sha256=sha(ROOT/'scripts/stage7a_bench/native_review_sheets_v2.py'))
        write_json(dest/(row['event_id']+'.json'),record)
        records.append(record)
        print(json.dumps({k:record[k] for k in ('index','event_id','prompt','release_answer','reference_only','files')},ensure_ascii=False),flush=True)
    return records


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',required=True)
    parser.add_argument('--start',type=int,required=True)
    parser.add_argument('--end',type=int,required=True)
    args=parser.parse_args()
    render(args.manifest,args.start,args.end)
