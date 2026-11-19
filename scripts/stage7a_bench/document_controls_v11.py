"""Apply reviewed local pixels while preserving every native PDF page.

Source images must match the original native page's decoded hash. At runtime
all PDF pages are rendered in order; only the named reviewed page is replaced.
No evidence-page selection, crop, prompt rewrite or native generation occurs.
"""
from copy import deepcopy
import hashlib

import pypdfium2 as pdfium

from scripts.stage7a.common import sha
from scripts.stage7a_bench.causal_provenance_v2 import stage_path
from scripts.stage7a_bench.document_inputs_v2 import assemble, prepare_document
from scripts.stage7a_bench.image_inputs_v2 import describe, load_asset, prepare_condition


def checked_source_page(entry, asset):
    path = stage_path(asset['path'], 'causal_pilot/source_review_sheets')
    actual = describe(dict(kind='file', path=str(path), slot=asset['slot']), path.read_bytes())
    if actual != asset:
        raise ValueError('Document source-page asset changed')
    pages = [p for p in entry['native_input']['visual_images'] if p['slot'] == asset['slot']]
    if (len(pages) != 1 or pages[0]['image_size'] != asset['size'] or
            pages[0]['decoded_image_sha256'] != asset['decoded_sha256']):
        raise ValueError('Source PNG does not equal the original native PDF page')
    if sha(entry['row']['document_path']) != entry['row']['document_sha256']:
        raise ValueError('Frozen source PDF changed')
    return actual


def override_row(entry, source, variant):
    source = checked_source_page(entry, source)
    if source['slot'] != variant['slot'] or source['size'] != variant['size']:
        raise ValueError('Control changed the source page identity or dimensions')
    row = deepcopy(entry['row'])
    row['document_page_overrides'] = [dict(slot=source['slot'],
        original_decoded_sha256=source['decoded_sha256'], asset=variant)]
    return row


def verify_document_control_geometry(native, changed, row):
    for key in ('document_path', 'document_sha256', 'renderer_version', 'render_scale'):
        if native[key] != changed[key] or native[key] != row[key]:
            raise ValueError('Local control changed native PDF identity: '+key)
    overrides = {v['slot']:v for v in row['document_page_overrides']}
    left, right = native['visual_images'], changed['visual_images']
    if len(left) != len(right):
        raise ValueError('Local control removed a native PDF page')
    for before, after in zip(left, right):
        expected = deepcopy(before)
        if before['slot'] in overrides:
            expected['decoded_image_sha256'] = overrides[before['slot']]['asset']['decoded_sha256']
        if after != expected:
            raise ValueError('Local control changed another page, page order or metadata')


def prepare_control_condition(processor, row, device):
    if not row.get('document_path'):
        return prepare_condition(processor, row, device)
    if not row.get('document_page_overrides'):
        return prepare_document(processor, row, device)
    if sha(row['document_path']) != row['document_sha256']:
        raise ValueError('Frozen PDF hash changed')
    if str(pdfium.PYPDFIUM_INFO) != row['renderer_version']:
        raise ValueError('Frozen PDF renderer changed')
    values = row['document_page_overrides']
    overrides = {v['slot']:v for v in values}
    allowed = {f'page_{i+1}' for i in range(row['page_count'])}
    if len(values) != 1 or len(overrides) != 1 or not set(overrides) <= allowed:
        raise ValueError('Each reviewed control replaces exactly one native page')

    def pages():
        with pdfium.PdfDocument(row['document_path']) as doc:
            if len(doc) != row['page_count']:
                raise ValueError('Frozen PDF page count changed')
            for index in range(len(doc)):
                page = doc[index]
                bitmap = page.render(scale=row['render_scale'])
                image = bitmap.to_pil().convert('RGB').copy()
                bitmap.close()
                page.close()
                slot = f'page_{index+1}'
                if slot in overrides:
                    override = overrides[slot]
                    asset = override['asset']
                    if (hashlib.sha256(image.tobytes()).hexdigest() != override['original_decoded_sha256'] or
                            asset['slot'] != slot or asset['size'] != list(image.size)):
                        image.close()
                        raise ValueError('Reviewed control does not match this original PDF page')
                    stage_path(asset['path'], 'causal_pilot/edit_bank')
                    image.close()
                    image = load_asset(asset)
                meta = dict(image_size=list(image.size),
                    decoded_image_sha256=hashlib.sha256(image.tobytes()).hexdigest())
                item = processor.image_processor(images=[image], return_tensors='pt')
                image.close()
                yield item, meta

    batch, meta = assemble(processor, row['prompt'], pages(), device)
    meta.update(event_id=row['event_id'], condition=row['condition'],
        document_path=row['document_path'], document_sha256=row['document_sha256'],
        renderer_version=row['renderer_version'], render_scale=row['render_scale'])
    return batch, meta
