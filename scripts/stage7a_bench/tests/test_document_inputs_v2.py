import hashlib

import torch
from PIL import Image
from transformers import AutoProcessor

from scripts.stage7a.common import ROOT, read_json, configure_fresh_processor
from scripts.stage7a_bench.document_inputs_v2 import assemble


def test_streamed_pages_equal_canonical_processor_with_mixed_shapes():
    checkpoint = read_json(ROOT / 'outputs/stage7a_bench_v2/config/runtime.json')['model_checkpoint']
    processor = AutoProcessor.from_pretrained(checkpoint, local_files_only=True)
    configure_fresh_processor(processor)
    pages = [Image.new('RGB', (352, 256), 'red'), Image.new('RGB', (288, 416), 'blue')]
    prompt = 'Compare the first page with the second page.'
    content = [{'type': 'image', 'image': image} for image in pages] + [{'type': 'text', 'text': prompt}]
    expected = processor.apply_chat_template([{'role': 'user', 'content': content}], tokenize=True,
        add_generation_prompt=True, return_dict=True, return_tensors='pt')
    def stream():
        for image in pages:
            yield processor.image_processor(images=[image], return_tensors='pt'), dict(image_size=list(image.size),
                decoded_image_sha256=hashlib.sha256(image.tobytes()).hexdigest())
    actual, meta = assemble(processor, prompt, stream(), 'cpu')
    assert actual.keys() == expected.keys()
    for key in actual:
        assert torch.equal(actual[key], expected[key]), key
    assert meta['image_order'] == ['page_1', 'page_2']
    assert meta['visual_images'][0]['image_size'] == [352, 256]
    assert meta['visual_images'][1]['image_size'] == [288, 416]
