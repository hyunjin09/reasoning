"""Full-PDF native inputs, one page of CPU preprocessing at a time.

No annotated evidence pages, question retrieval, page truncation or raw cache.
Uses the installed processor's own replacement/token-type methods. Tensor
parity against apply_chat_template is required before GPU inference.
"""
import hashlib

import torch
import pypdfium2 as pdfium

from scripts.stage7a.common import sha
from visual_reasoning.stage0.attention import visual_grid_metadata


def assemble(processor, prompt, processed_pages, device):
    pixels, grids, page_meta = [], [], []
    for item, meta in processed_pages:
        if tuple(item['image_grid_thw'].shape) != (1, 3):
            raise ValueError('Expected one grid per PDF page')
        pixels.append(item['pixel_values'].to(device))
        grids.append(item['image_grid_thw'][0].tolist())
        page_meta.append(meta)
    if not grids:
        raise ValueError('Empty document')
    grid = torch.tensor(grids, dtype=torch.long)
    content = [{'type': 'image'} for _ in grids] + [{'type': 'text', 'text': prompt}]
    chat = processor.apply_chat_template([{'role': 'user', 'content': content}], tokenize=False,
                                         add_generation_prompt=True)
    replacements = [processor.replace_image_token({'image_grid_thw': grid}, i) for i in range(len(grids))]
    texts, _ = processor.get_text_with_replacements([chat], replacements, [], [])
    batch = processor.tokenizer(texts, return_tensors='pt', padding=False, return_token_type_ids=False)
    processor._check_special_mm_tokens(texts, batch, modalities=['image', 'video', 'audio'])
    batch['mm_token_type_ids'] = torch.as_tensor(processor.create_mm_token_type_ids(batch['input_ids']))
    batch['pixel_values'] = torch.cat(pixels, dim=0)
    del pixels
    batch['image_grid_thw'] = grid
    ids = batch['input_ids'][0]
    visual = (ids == int(processor.image_token_id)).nonzero().flatten().tolist()
    segments, offset = [], 0
    for index, (g, meta) in enumerate(zip(grids, page_meta)):
        mapping = visual_grid_metadata(g, processor.image_processor.merge_size, processor.image_processor.patch_size)
        count = mapping['visual_token_count']
        positions = visual[offset:offset + count]
        if len(positions) != count or positions[-1] - positions[0] + 1 != count:
            raise ValueError('PDF page token mapping mismatch')
        segments.append(dict(**meta, slot=f'page_{index+1}', physical_page=index+1,
            image_grid_thw=g, visual_mapping=mapping, visual_token_indices=positions))
        offset += count
    if offset != len(visual):
        raise ValueError('Unmapped PDF image tokens')
    meta = dict(prompt=prompt, prompt_token_ids=ids.tolist(), prompt_token_count=len(ids),
        visual_token_indices=visual, image_order=[s['slot'] for s in segments], visual_images=segments,
        image_grid_thw=grids, image_size=None, image_path=None, visual_mapping=None,
        decoded_image_sha256=None, no_image=False, image_state_policy='Fresh full PDF, all physical pages in original order')
    return {k: v.to(device) for k, v in batch.items()}, meta


def prepare_document(processor, row, device):
    if sha(row['document_path']) != row['document_sha256']:
        raise ValueError('Frozen PDF hash changed')
    if str(pdfium.PYPDFIUM_INFO) != row['renderer_version']:
        raise ValueError('Frozen PDF renderer changed')
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
                meta = dict(image_size=list(image.size), decoded_image_sha256=hashlib.sha256(image.tobytes()).hexdigest())
                item = processor.image_processor(images=[image], return_tensors='pt')
                image.close()
                yield item, meta
    batch, meta = assemble(processor, row['prompt'], pages(), device)
    meta.update(event_id=row['event_id'], condition=row['condition'],
        document_path=row['document_path'], document_sha256=row['document_sha256'],
        renderer_version=row['renderer_version'], render_scale=row['render_scale'])
    return batch, meta
