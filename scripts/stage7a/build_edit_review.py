"""Construct proposed edits and enlarged source/sham/counterfactual review sheets."""
import hashlib
import argparse
import math
import numpy as np
from PIL import Image, ImageDraw
from scipy.fft import dctn
from scripts.stage7a.common import ROOT, OUT, read_json, read_jsonl, write_json
from scripts.stage6a.review_candidates import open_image
from visual_reasoning.stage7a.edits import render_text_pair


def identity(image):
    width, height = image.size
    digest = hashlib.sha256(f'{width}x{height}:'.encode() + image.tobytes()).hexdigest()
    gray = np.asarray(image.convert('L').resize((32, 32), Image.Resampling.LANCZOS), dtype=float)
    low = dctn(gray, norm='ortho')[:8, :8].flatten()
    bits = low > np.median(low[1:])
    bits[0] = False
    phash = sum(int(b) << i for i, b in enumerate(bits))
    return dict(width=width, height=height, decoded_stimulus_sha256=digest, phash=f'{phash:016x}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', nargs='+', help='Rebuild only changed proposals; retain other audited records')
    args = parser.parse_args()
    rows = {r['base_id']: r for r in read_jsonl(OUT / 'cohort/source_candidate_order.jsonl')}
    definitions = read_json(OUT / 'annotations/provisional_source_definitions.json')
    historical = read_jsonl(ROOT / 'outputs/stage6a/audit/source_identity_catalog.jsonl')
    records = []
    previous = {r['base_id']: r for r in read_json(OUT/'audit/proposed_source_edits.json')} if args.only else {}
    for key, definition in definitions.items():
        if args.only and key not in args.only:
            records.append(previous[key])
            continue
        image = open_image(rows[key])
        ident = identity(image)
        near = [r['base_id'] for r in historical if (
            r['decoded_stimulus_sha256'] == ident['decoded_stimulus_sha256'] or
            (abs(math.log((r['width']/r['height'])/(image.width/image.height))) <= .15
             and (int(r['phash'],16)^int(ident['phash'],16)).bit_count() <= 4))]
        dest = OUT / 'assets' / key
        dest.mkdir(parents=True, exist_ok=True)
        image.save(dest / 'condition__intact.png')
        pairs = {}
        record = dict(base_id=key, identity=ident, historical_near_candidates=near, fields={})
        for role in ['T', 'X']:
            fact = definition[role]
            roi = fact.get('roi') or [round(value * (image.width if i % 2 == 0 else image.height))
                   for i, value in enumerate(fact['normalized_roi'])]
            try:
                prefix, suffix = fact.get('render_prefix', ''), fact.get('render_suffix', '')
                pair, audit = render_text_pair(image, roi, prefix+fact['value']+suffix,
                                              prefix+fact['counterfactual']+suffix,
                                              light_foreground=fact.get('light_foreground',False))
                for strip in fact.get('preserve_native_boxes', []):
                    for edited in pair.values():
                        edited.paste(image.crop(strip), tuple(strip[:2]))
                audit['preserved_native_boxes'] = fact.get('preserve_native_boxes', [])
                for name, edited in pair.items():
                    edited.save(dest / f'condition__{role}_{name}.png')
                pairs[role] = pair
                record['fields'][role] = {**fact, 'roi':roi, 'audit':audit}
            except ValueError as exc:
                record['fields'][role] = {**fact, 'roi':roi, 'construction_error':str(exc)}
                pairs[role] = {'sham': image, 'semantic': image}
        records.append(record)
        sheet = Image.new('RGB', (1200, 430), 'white')
        draw = ImageDraw.Draw(sheet)
        draw.text((5, 5), key + ' source / matched sham / semantic edit', fill='black')
        for j, role in enumerate(['T', 'X']):
            roi = record['fields'][role]['roi']
            pad = max(4, (roi[3]-roi[1])//2)
            box = [max(0,roi[0]-pad),max(0,roi[1]-pad),min(image.width,roi[2]+pad),min(image.height,roi[3]+pad)]
            field = definition[role]
            draw.text((5, 30+j*195), f"{role}: {field['entity']} {field['value']} -> {field['counterfactual']} ROI={roi}", fill='black')
            for i, view in enumerate([image, pairs[role]['sham'], pairs[role]['semantic']]):
                crop = view.crop(box)
                scale = min(6, 380/crop.width, 150/crop.height)
                crop = crop.resize((round(crop.width*scale), round(crop.height*scale)))
                sheet.paste(crop, (i*400+8, 52+j*195))
        sheet.save(OUT / 'review' / (key+'_edits.png'))
    write_json(OUT / 'audit/proposed_source_edits.json', records)
    # Combine four review strips per image; source sheets preserve full context.
    for offset in range(0,len(records),4):
        part=records[offset:offset+4]
        sheet=Image.new('RGB',(1200,430*len(part)),'white')
        for i,r in enumerate(part):
            sheet.paste(Image.open(OUT/'review'/(r['base_id']+'_edits.png')),(0,430*i))
        sheet.save(OUT/'review'/f'edit_batch_{offset//4:02d}.png')
    print('Proposed',len(records),'historical near-image candidates',sum(bool(r['historical_near_candidates']) for r in records))


if __name__ == '__main__':
    main()
