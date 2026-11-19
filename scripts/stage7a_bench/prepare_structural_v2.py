"""Freeze output-blind audit IDs and render source documents for manual review.

No model outputs or causal effects are read. Page annotations are candidate
locations, never treated as verified physical-page mappings automatically.
"""
import argparse
import ast
import datetime
import hashlib
import io
import json
import textwrap
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pyarrow.parquet as pq
import pypdfium2 as pdfium
from PIL import Image

from scripts.stage7a.common import read_json, read_jsonl, sha, write_json, write_jsonl

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/stage7a_bench_v2'
SEED = 'stage7a_bench_20260911'


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def inventory_row(name):
    return next(r for r in read_json(OUT / 'cohort/dataset_inventory.json')['candidates']
                if r['candidate_id'] == name)


def metadata_rows(name):
    item = inventory_row(name)
    base = Path(item['local_path'])
    rows = []
    if name == 'mathsight':
        source = Path(item['annotation_path'])
        for index, raw in enumerate(read_jsonl(source)):
            image = raw['image_path']
            qid = digest(image + '|' + raw['question'])[:20]
            rows.append(dict(benchmark=name, example_id=qid, row_index=index,
                family_id='mathsight_' + Path(image).stem, question=raw['question'],
                answer_preview=str(raw['ground_truth'] or raw['answer/solution'])[:1600],
                full_answer_source=str(source), answer_field='ground_truth or answer/solution',
                subject=raw['subject'], image_path=str(base / 'Dataset/Orig' / image),
                hand_image_path=str(base / 'Dataset/hand' / image),
                photo_image_path=str(base / 'Dataset/photo' / image),
                annotation_source=str(source), question_sha256=digest(raw['question'])))
    elif name == 'charxiv':
        source = Path(item['annotation_path'])
        parquet = pq.ParquetFile(source)
        columns = [c for c in parquet.schema_arrow.names if c != 'image']
        for index, raw in enumerate(parquet.read(columns=columns).to_pylist()):
            rows.append(dict(benchmark=name, example_id=raw['figure_path'], row_index=index,
                family_id=raw['original_id'], question=raw['reasoning_q'], answer_preview=raw['reasoning_a'],
                subject=raw['category'], annotation_source=str(source), image_column='image',
                source_metadata=raw))
    elif name == 'mmlongbench_doc':
        source = Path(item['annotation_path'])
        for index, raw in enumerate(pq.read_table(source).to_pylist()):
            pages = ast.literal_eval(raw['evidence_pages'])
            path = base / 'documents' / raw['doc_id']
            rows.append(dict(benchmark=name, example_id=digest(raw['doc_id'] + '|' + raw['question'])[:20] + f'_row{index}',
                row_index=index, family_id=raw['doc_id'], question=raw['question'],
                answer_preview=raw['answer'], evidence_pages=pages,
                evidence_sources=ast.literal_eval(raw['evidence_sources']),
                subject=raw['doc_type'], document_path=str(path), document_available=path.is_file(),
                annotation_source=str(source), page_mapping_status='UNVERIFIED_RELEASE_ANNOTATION'))
    elif name == 'mmmu_pro':
        source = Path(item['annotation_path'])
        for file in sorted(source.glob('*.parquet')):
            parquet = pq.ParquetFile(file)
            columns = [c for c in parquet.schema_arrow.names if not c.startswith('image_')]
            for index, raw in enumerate(parquet.read(columns=columns).to_pylist()):
                rows.append(dict(benchmark=name, example_id=raw['id'], row_index=index,
                    family_id=raw['id'], question=raw['question'], options=ast.literal_eval(raw['options']),
                    answer_preview=raw['answer'], subject=raw['subject'],
                    annotation_source=str(file), source_metadata=raw,
                    image_columns=[f'image_{i}' for i in range(1, 8)]))
    elif name == 'phantom_0':
        source = Path(item['annotation_path'])
        for index, raw in enumerate(read_json(source)):
            rows.append(dict(benchmark=name, example_id=raw['id'], row_index=index,
                family_id=raw['category'], question=raw['question'], answer_preview=None,
                subject=raw['domain'], question_type=raw['question_type'],
                annotation_source=str(source), no_image_by_design=True,
                ground_truth_scope='No real image or factual answer; evaluate evidence-absence behavior only.'))
    elif name == 'medxpertqa_mm':
        source = Path(item['annotation_path'])
        for index, raw in enumerate(read_jsonl(source)):
            rows.append(dict(benchmark=name, example_id=raw['id'], row_index=index,
                family_id=raw['id'], question=raw['question'], options=raw['options'],
                answer_preview=raw['label'], subject=raw['body_system'],
                annotation_source=str(source), image_archive=str(base / 'images.zip'),
                archive_image_members=['images/' + x for x in raw['images']],
                medical_task=raw['medical_task'], question_type=raw['question_type']))
    elif name == 'microvqa':
        for file in sorted(Path(item['annotation_path']).glob('test-*.parquet')):
            parquet = pq.ParquetFile(file)
            columns = ['key_question', 'key_image', 'question', 'choices', 'correct_index',
                       'correct_answer', 'task_str', 'image_caption', 'context_image_generation']
            for index, raw in enumerate(parquet.read(columns=columns).to_pylist()):
                rows.append(dict(benchmark=name, example_id=str(raw['key_question']), row_index=index,
                    family_id='microvqa_image_' + str(raw['key_image']), question=raw['question'],
                    options=raw['choices'], answer_preview=raw['correct_answer'],
                    correct_index=raw['correct_index'], subject=raw['task_str'],
                    annotation_source=str(file), image_column='images_list',
                    release_caption=raw['image_caption'], release_context=raw['context_image_generation']))
    else:
        raise ValueError(name)
    ids = [r['example_id'] for r in rows]
    assert len(set(ids)) == len(ids), 'Ambiguous official question identity: ' + name
    for row in rows:
        row['selection_key'] = digest(SEED + '|' + name + '|' + row['example_id'])
    return sorted(rows, key=lambda r: r['selection_key'])


def freeze(name):
    rows = metadata_rows(name)
    path = OUT / 'cohort/benchmark_manifests' / (name + '_structural.jsonl')
    write_jsonl(path, rows[:64], freeze=True)
    order = [{k: r[k] for k in ['benchmark', 'example_id', 'family_id', 'row_index',
                              'annotation_source', 'selection_key']} for r in rows]
    write_jsonl(OUT / 'cohort/benchmark_manifests' / (name + '_prospective_order.jsonl'), order, freeze=True)
    state_path = OUT / 'cohort/sample_freeze.json'
    state = read_json(state_path)
    assert not state['model_generation_started']
    entry = dict(manifest=str(path.relative_to(ROOT)), sha256=sha(path), count=min(64, len(rows)),
        pool_size=len(rows), selection='First64 SHA256(seed|benchmark|stable question ID); no model outputs',
        seed=SEED, frozen_at=datetime.datetime.now().astimezone().isoformat())
    if name in state['structural']:
        assert state['structural'][name]['sha256'] == entry['sha256']
    else:
        state['structural'][name] = entry
        write_json(state_path, state)
    print('FROZEN', name, len(rows), sha(path), flush=True)


def embedded_images(row, cache):
    path = row['annotation_source']
    if cache.get('path') != path:
        cache.clear()
        columns = row.get('image_columns', [row['image_column']] if 'image_column' in row else [])
        cache.update(path=path, table=pq.read_table(path, columns=columns))
    result = []
    for column in cache['table'].column_names:
        value = cache['table'][column][row['row_index']].as_py()
        for image_index, asset in enumerate(value if isinstance(value, list) else [value]):
            if asset is None:
                continue
            if not asset.get('bytes'):
                raise ValueError('Embedded image bytes unavailable')
            image = Image.open(io.BytesIO(asset['bytes'])).convert('RGB')
            image.load()
            result.append((f'{column}[{image_index}]', image))
    return result


def document_images(row):
    if not row['document_available']:
        return [], dict(status='UNAVAILABLE', evidence_pages=row['evidence_pages'])
    result, bad = [], []
    with pdfium.PdfDocument(row['document_path']) as doc:
        count = len(doc)
        for number in row['evidence_pages']:
            if not isinstance(number, int) or not 1 <= number <= count:
                bad.append(number)
                continue
            page = doc[number - 1]
            bitmap = page.render(scale=1.6)
            image = bitmap.to_pil().convert('RGB').copy()
            result.append((f'Candidate physical page {number}/{count}; mapping UNVERIFIED', image))
            bitmap.close()
            page.close()
    return result, dict(status='RENDERED_CANDIDATE_PAGES', page_count=count,
                       evidence_pages=row['evidence_pages'], out_of_range_annotations=bad)


def render(name, start, end):
    rows = read_jsonl(OUT / 'cohort/benchmark_manifests' / (name + '_structural.jsonl'))
    dest = OUT / 'structural_audit/review_sheets'
    dest.mkdir(parents=True, exist_ok=True)
    cache, integrity = {}, []
    for n in range(start, min(end, len(rows))):
        row = rows[n]
        if name == 'mathsight':
            images = [(label, Image.open(row[field]).convert('RGB')) for label, field in
                      [('original', 'image_path'), ('hand', 'hand_image_path'), ('photo', 'photo_image_path')]]
            info = dict(status='THREE_VARIANTS_RENDERED')
        elif name == 'mmlongbench_doc':
            images, info = document_images(row)
        elif name == 'phantom_0':
            images, info = [], dict(status='NO_IMAGE_BY_DESIGN')
        elif name == 'medxpertqa_mm':
            with zipfile.ZipFile(row['image_archive']) as archive:
                images = [(member, Image.open(io.BytesIO(archive.read(member))).convert('RGB'))
                          for member in row['archive_image_members']]
            info = dict(status='VERIFIED_ARCHIVE_IMAGES_RENDERED')
        else:
            images, info = embedded_images(row, cache), dict(status='EMBEDDED_IMAGES_RENDERED')
        chunks = [images[i:i + 3] for i in range(0, len(images), 3)] or [[]]
        for part, chunk in enumerate(chunks):
            fig, axes = plt.subplots(1, max(1, len(chunk)), figsize=(16, 10), dpi=115, squeeze=False)
            for ax in axes.flat:
                ax.set_axis_off()
            for ax, (label, image) in zip(axes.flat, chunk):
                ax.imshow(image)
                ax.set_title(label, fontsize=10)
            question = row['question']
            if row.get('options') and 'Answer Choices:' not in question:
                options = row['options']
                pairs = options.items() if isinstance(options, dict) else [(chr(65+i), x) for i, x in enumerate(options)]
                question += '\n' + ' | '.join(f'{k}: {x}' for k, x in pairs)
            header = f"{n:02d} {name} {row['example_id']} | {row['subject']}\n"
            header += textwrap.fill(question, 170)
            answer = textwrap.fill('RELEASE ANSWER: ' + str(row['answer_preview']), 170)
            # Full questions/answer provenance remain in the manifest. Long proof
            # answers are reviewed from the original annotation, not this sheet.
            fig.text(.02, .98, header, va='top', fontsize=9, parse_math=False)
            fig.text(.02, .015, answer[:1000], va='bottom', fontsize=8, parse_math=False)
            if not chunk:
                axes[0, 0].text(.1, .5, 'No candidate evidence page available.\n' + json.dumps(info),
                                transform=axes[0, 0].transAxes, fontsize=10, wrap=True)
            question_lines = len(header.splitlines())
            fig.subplots_adjust(top=max(.45, .91 - .016 * question_lines), bottom=.16, wspace=.08)
            fig.savefig(dest / f'{name}_{n:02d}_{part}.png')
            plt.close(fig)
        integrity.append(dict(example_id=row['example_id'], row=n, images=len(images),
            chunks=len(chunks), **info))
        print('RENDERED', name, n, len(images), flush=True)
    write_json(OUT / 'audit' / f'{name}_render_{start}_{end}.json', dict(
        source_outputs_read=False, checks=integrity, renderer_sha256=sha(__file__),
        pdf_api_source='https://pypdfium2.readthedocs.io/en/stable/python_api.html'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--benchmark', choices=['mathsight', 'charxiv', 'mmlongbench_doc', 'mmmu_pro',
                                               'phantom_0', 'microvqa', 'medxpertqa_mm'], required=True)
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=64)
    args = parser.parse_args()
    freeze(args.benchmark)
    if args.render:
        render(args.benchmark, args.start, args.end)


if __name__ == '__main__':
    main()
