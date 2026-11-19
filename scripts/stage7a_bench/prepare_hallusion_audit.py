"""Freeze an output-blind structural sample and render diagnostic review sheets.

Read existing Arrow assets directly. Sheets are annotated review artifacts, not
an extracted raw-image cache. No model is loaded and no native outputs are read.
"""
import hashlib
import io
import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pyarrow as pa
from PIL import Image

from scripts.stage7a.common import read_json, sha, write_json, write_jsonl

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/stage7a_bench'
SEED = 'stage7a_bench_20260911'


def main():
    inventory = read_json(OUT / 'cohort/dataset_inventory.json')
    candidate = next(r for r in inventory['candidates']
                     if r['candidate_id'] == 'hallusionbench')
    assert candidate['usable']
    source = Path(candidate['annotation_path']).resolve()
    assert source.is_relative_to(Path('/data/dataset'))
    table = pa.ipc.open_stream(pa.memory_map(str(source), 'r')).read_all()
    rows = table.drop(['image']).to_pylist()
    for index, row in enumerate(rows):
        row.update(row_index=index, benchmark='hallusionbench',
                   example_id='_'.join(row[k] for k in
                       ['category', 'subcategory', 'set_id', 'figure_id', 'question_id']))
        row['family_id'] = '_'.join(row[k] for k in ['category', 'subcategory', 'set_id'])
        row['selection_key'] = hashlib.sha256(
            (SEED + '|' + row['example_id']).encode()).hexdigest()
    assert len({r['example_id'] for r in rows}) == len(rows)
    rows.sort(key=lambda r: r['selection_key'])
    sample = rows[:64]
    rules = dict(seed=SEED, sample_size=64, sampling_unit='question-image example',
        selection='First64 of SHA256(seed|official composite ID) order over951 image rows.',
        family_unit='category/subcategory/set_id; retain shared-image dependence',
        model_outputs_read=False, source_scores={
            'S0': 'source not localizable', 'S1': 'coarse source only',
            'S2': 'localizable target but weak alternative identity',
            'S3': 'target and plausible alternatives localizable',
            'S4': 'target and alternatives independently editable'},
        readout_scores={'R0': 'no clean local readout', 'R1': 'final-answer only',
            'R2': 'value readout', 'R3': 'binding/source readout',
            'R4': 'value + binding + error-oriented readout'},
        stop_rule='S3/S4 <20% AND R3/R4 <20%, unless verified unique paired property',
        binary_scope='A yes/no answer alone does not imply an explicit local binding/value claim.',
        tier_b_reason=inventory['tier_b_activation_reason'])
    write_json(OUT / 'config/structural_audit_rules.json', rules, freeze=True)
    manifest = OUT / 'cohort/benchmark_manifests/hallusionbench_structural.jsonl'
    write_jsonl(manifest, sample, freeze=True)
    write_json(OUT / 'cohort/sample_freeze.json', dict(
        structural=dict(hallusionbench=dict(manifest=str(manifest.relative_to(ROOT)),
            sha256=sha(manifest), count=len(sample), source=str(source), source_sha256=sha(source))),
        native_screen={}, causal_pilot={}, model_generation_started=False), freeze=True)

    dest = OUT / 'structural_audit/review_sheets'
    dest.mkdir(parents=True, exist_ok=True)
    checks = []
    for page in range(16):
        fig, axes = plt.subplots(2, 2, figsize=(16, 14), dpi=130)
        for offset, ax in enumerate(axes.flat):
            n = page * 4 + offset
            row = sample[n]
            raw = table['image'][row['row_index']].as_py()['bytes']
            image = Image.open(io.BytesIO(raw)).convert('RGB')
            image.load()
            checks.append(dict(example_id=row['example_id'], image_dimensions=list(image.size),
                image_bytes_sha256=hashlib.sha256(raw).hexdigest(), decode_ok=True))
            ax.imshow(image)
            ax.set_axis_off()
            title = (f"{n:02d} {row['example_id']} | GT={row['gt_answer']}\n" +
                     textwrap.fill(row['question'], 82) + '\n' +
                     textwrap.fill('Annotation: ' + row['gt_answer_details'], 82))
            ax.set_title(title, fontsize=9, loc='left', pad=10)
        fig.suptitle('HallusionBench — frozen structural audit; no model outputs', fontsize=14)
        fig.tight_layout(rect=(0, 0, 1, .97), h_pad=3)
        fig.savefig(dest / f'hallusionbench_{page:02d}.png')
        plt.close(fig)
    write_json(OUT / 'audit/hallusionbench_structural_input_integrity.json', dict(
        passed=all(x['decode_ok'] for x in checks), expected=64, checked=len(checks),
        manifest_sha256=sha(manifest), checks=checks,
        source_outputs_read=False, image_or_annotation_modified=False), freeze=True)
    print(json.dumps(dict(frozen=len(sample), families=len({r['family_id'] for r in sample}),
        images=len({r['filename'] for r in sample}), review_sheets=16,
        manifest_sha256=sha(manifest))))


if __name__ == '__main__':
    main()
