"""CPU integration check with the actual processor and a two-page PDF."""
from copy import deepcopy

from PIL import Image, ImageDraw, JpegImagePlugin
import pypdfium2 as pdfium
import torch
from transformers import AutoProcessor

from scripts.stage7a.common import ROOT, read_json, write_json, sha, configure_fresh_processor
from scripts.stage7a_bench.document_inputs_v2 import prepare_document
from scripts.stage7a_bench.document_controls_v11 import (
    checked_source_page, override_row, prepare_control_condition, verify_document_control_geometry,
)
from scripts.stage7a_bench.image_inputs_v2 import describe


def main():
    base = ROOT / 'outputs/stage7a_bench_v2'
    dest = base / 'audit/document_controls_v11_cpu_fixture_retry2'
    dest.mkdir(exist_ok=False)
    pages = []
    for value in ('12', '34'):
        image = Image.new('RGB', (256, 256), 'white')
        ImageDraw.Draw(image).text((80, 80), value, fill='black')
        pages.append(image)
    path = dest / 'two_pages.pdf'
    pages[0].save(path, save_all=True, append_images=pages[1:])
    row = dict(event_id='cpu_fixture', condition='image_present', document_path=str(path),
        document_sha256=sha(path), renderer_version=str(pdfium.PYPDFIUM_INFO), render_scale=1.6,
        page_count=2, prompt='Read the first page.', no_image=False)
    processor = AutoProcessor.from_pretrained(read_json(base / 'config/runtime_node02_v3.json')['model_checkpoint'],
        local_files_only=True)
    configure_fresh_processor(processor)
    native, meta = prepare_document(processor, row, 'cpu')
    with pdfium.PdfDocument(path) as doc:
        page = doc[0]
        bitmap = page.render(scale=1.6)
        image = bitmap.to_pil().convert('RGB').copy()
        bitmap.close()
        page.close()
    source_dir = base / 'causal_pilot/source_review_sheets/cpu_document_control_fixture_v11'
    source_dir.mkdir(exist_ok=False)
    source_path = source_dir / 'page_001.png'
    image.save(source_path)
    source = describe(dict(kind='file', path=str(source_path), slot='page_1'), source_path.read_bytes())
    entry = dict(row=row, native_input=meta)
    assert checked_source_page(entry, source) == source
    edit_dir = base / 'causal_pilot/edit_bank/cpu_document_control_fixture_v11'
    edit_dir.mkdir(exist_ok=False)
    edit_path = edit_dir / 'changed.png'
    ImageDraw.Draw(image).rectangle((40, 40, 55, 55), fill='black')
    image.save(edit_path)
    variant = describe(dict(kind='file', path=str(edit_path), slot='page_1'), edit_path.read_bytes())
    changed_row = override_row(entry, source, variant)
    changed, changed_meta = prepare_control_condition(processor, changed_row, 'cpu')
    verify_document_control_geometry(meta, changed_meta, changed_row)
    assert torch.equal(native['input_ids'], changed['input_ids'])
    assert torch.equal(native['image_grid_thw'], changed['image_grid_thw'])
    assert meta['visual_images'][1] == changed_meta['visual_images'][1]
    assert not torch.equal(native['pixel_values'], changed['pixel_values'])
    half = native['pixel_values'].shape[0]//2
    assert torch.equal(native['pixel_values'][half:], changed['pixel_values'][half:])
    rejected = []
    changes = [
        ('foreign_slot', lambda r: r['document_page_overrides'][0].update(slot='page_3')),
        ('original_digest', lambda r: r['document_page_overrides'][0].update(original_decoded_sha256='0'*64)),
        ('duplicate_page', lambda r: r['document_page_overrides'].append(deepcopy(r['document_page_overrides'][0]))),
        ('pdf_hash', lambda r: r.update(document_sha256='0'*64)),
    ]
    for label, mutate in changes:
        bad = deepcopy(changed_row)
        mutate(bad)
        try:
            prepare_control_condition(processor, bad, 'cpu')
        except ValueError:
            rejected.append(label)
        else:
            raise AssertionError('Expected rejection: '+label)
    original = read_json(base / 'audit/mmlong_v9_oom_continuation_handoff_20260914.json')['new_live_dependency_sha256']
    assert all(sha(ROOT / name) == digest for name, digest in original.items())
    write_json(base / 'audit/document_controls_v11_cpu_validation.json', dict(
        status='PASS_ACTUAL_PROCESSOR_TWO_PAGE_GEOMETRY', native_prompt_tokens=meta['prompt_token_count'],
        full_page_order_and_count_preserved=True, unchanged_page_pixels_exact=True,
        changed_page_pixels_differ=True, original_source_png_matches_native=True,
        rejected_mutations=rejected, native_dependencies_preserved=len(original), cuda_used=False,
        initial_fixture_failure='Pillow PDF writer JPEG plugin was not registered; explicit installed plugin import fixes fixture setup. No scientific input or runtime failed.'), freeze=True)
    print('PASS actual processor full-page control and four corruption guards; no CUDA.')


if __name__ == '__main__':
    main()
