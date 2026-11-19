"""Locate candidate pages for output-blind structural review, never inference.

Text matching only selects manual review pages. It is not a retrieval model or
an absence/correctness certificate, and is never supplied to native prompts.
"""
import argparse
import re
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pypdfium2 as pdfium

from scripts.stage7a.common import read_jsonl, sha, write_json
from scripts.stage7a_bench.prepare_structural_v2 import OUT, document_images


def supplement(index, explicit_pages=None, tag='supp'):
    assert re.fullmatch(r'[a-z0-9_]+', tag)
    manifest = OUT / 'cohort/benchmark_manifests/mmlongbench_doc_structural.jsonl'
    row = read_jsonl(manifest)[index]
    stop = set('what which when where whose with from this that there these their have does many more only first page pages slide slides figure figures document report according answer please format'.split())
    words = sorted(set(re.findall(r'[a-z0-9]+', row['question'].lower())) - stop)
    words = [w for w in words if len(w) > 2 or w.isdigit()]
    texts = []
    with pdfium.PdfDocument(row['document_path']) as doc:
        for number in range(len(doc)):
            page = doc[number]
            textpage = page.get_textpage()
            texts.append(textpage.get_text_range())
            textpage.close()
            page.close()
    scores = [(sum(w in text.lower() for w in words), i + 1) for i, text in enumerate(texts)]
    ranked = sorted(scores, key=lambda pair: (-pair[0], pair[1]))[:3]
    pages = explicit_pages or sorted(p for score, p in ranked)
    images, info = document_images(dict(row, evidence_pages=pages))
    dest = OUT / 'structural_audit/review_sheets'
    for start in range(0, len(images), 3):
        chunk = images[start:start+3]
        fig, axes = plt.subplots(1, len(chunk), figsize=(18, 10), squeeze=False)
        for axis, (label, image) in zip(axes[0], chunk):
            axis.imshow(image)
            axis.axis('off')
            axis.set_title(label, fontsize=10)
            image.close()
        fig.suptitle(f'{index:02d} SUPPLEMENTARY AUDIT ONLY\n' + '\n'.join(textwrap.wrap(row['question'], 150)), fontsize=10)
        fig.text(.02, .02, 'RELEASE ANSWER: ' + str(row['answer_preview'])[:1000], fontsize=9)
        fig.savefig(dest / f'mmlongbench_doc_{index:02d}_{tag}_{start//3}.png', dpi=100)
        plt.close(fig)
    receipt = dict(index=index, example_id=row['example_id'], manifest_sha256=sha(manifest),
        document_sha256=sha(row['document_path']), query_terms=words, ranked_candidate_pages=ranked,
        rendered_pages=pages, page_count=len(texts), model_outputs_read=False,
        native_input_use=False, absence_certification=False, selection='Explicit audit pages' if explicit_pages else 'Top3 question-term overlap, ties by physical page')
    suffix = '' if tag == 'supp' else '_' + tag
    write_json(OUT / 'audit' / f'mmlong_supplement_{index:02d}{suffix}.json', receipt)
    print(index, pages, [(p, texts[p-1][:220].replace('\n', ' ')) for p in pages], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--indices', type=int, nargs='+', required=True)
    parser.add_argument('--pages', type=int, nargs='+')
    parser.add_argument('--tag', default='supp')
    args = parser.parse_args()
    for index in args.indices:
        supplement(index, args.pages, args.tag)
