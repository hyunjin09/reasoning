import hashlib
import io

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from PIL import Image

from scripts.stage7a_bench.image_inputs_v2 import image_assets, image_assets_many, load_asset, user_content


def png(color):
    stream = io.BytesIO()
    Image.new('RGB', (64, 64), color).save(stream, format='PNG')
    return stream.getvalue()


def test_parquet_row_and_list_index_preserved(tmp_path):
    path = tmp_path / 'images.parquet'
    red, blue = png('red'), png('blue')
    pq.write_table(pa.table({'images': [[{'bytes': red}], [{'bytes': blue}, {'bytes': red}]]}), path)
    assets = image_assets(dict(annotation_source=str(path), row_index=1, image_column='images'))
    assert len(assets) == 2
    assert assets[0]['bytes_sha256'] == hashlib.sha256(blue).hexdigest()
    assert load_asset(assets[0]).getpixel((0, 0)) == (0, 0, 255)
    assert load_asset(assets[1]).getpixel((0, 0)) == (255, 0, 0)
    rows = [dict(example_id='blue_row', annotation_source=str(path), row_index=1, image_column='images'),
            dict(example_id='red_row', annotation_source=str(path), row_index=0, image_column='images')]
    streamed = image_assets_many(rows)
    assert streamed['blue_row'] == assets
    assert streamed['red_row'] == image_assets(rows[1])
    assets[0]['bytes_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='payload hash'):
        load_asset(assets[0])


def test_markers_keep_shuffled_options_and_repeated_references():
    first, second = Image.new('RGB', (64, 64), 'red'), Image.new('RGB', (64, 64), 'blue')
    prompt = 'Choose A: <image 2> B: <image 1>. Compare <image 2> again.'
    row = dict(prompt=prompt, no_image=False, image_layout='inline_markers')
    content, order = user_content(row, [('image_1', first), ('image_2', second)])
    assert order == ['image_2', 'image_1', 'image_2']
    assert [p['image'] for p in content if p['type'] == 'image'] == [second, first, second]
    assert ''.join(p.get('text', '') for p in content) == 'Choose A:  B: . Compare  again.'


def test_absent_image_has_no_reused_pixels_and_preserves_text():
    row = dict(prompt='What is <image 1>?', no_image=True, image_layout='inline_markers')
    content, order = user_content(row, [])
    assert content == [{'type': 'text', 'text': row['prompt']}]
    assert order == []
    with pytest.raises(ValueError, match='No-image'):
        user_content(row, [('image_1', Image.new('RGB', (2, 2)))])


def test_missing_or_unused_marker_is_rejected():
    row = dict(prompt='<image 2>', no_image=False, image_layout='inline_markers')
    with pytest.raises(ValueError, match='missing'):
        user_content(row, [('image_1', Image.new('RGB', (2, 2)))])
    row['prompt'] = '<image 1>'
    with pytest.raises(ValueError, match='Unused'):
        user_content(row, [('image_1', Image.new('RGB', (2, 2))), ('image_2', Image.new('RGB', (2, 2)))])


def test_real_processor_matches_canonical_and_clears_image_state(tmp_path):
    import torch
    from transformers import AutoProcessor
    from scripts.stage7a.common import ROOT, configure_fresh_processor, read_json, sha
    from scripts.stage7a_bench.image_inputs_v2 import prepare_condition
    from visual_reasoning.stage6a.runtime import prepare_condition as canonical
    checkpoint = read_json(ROOT / 'outputs/stage7a_bench_v2/config/runtime.json')['model_checkpoint']
    processor = AutoProcessor.from_pretrained(checkpoint, local_files_only=True)
    configure_fresh_processor(processor)
    path = tmp_path / 'source.png'
    path.write_bytes(png('red'))
    original = dict(event_id='parity', condition='image_present', prompt='What color?',
                    image_path=str(path), image_sha256=sha(path), no_image=False)
    expected, old_meta = canonical(processor, original, 'cpu')
    embedded = dict(original, image_path=None, image_assets=image_assets(original))
    actual, meta = prepare_condition(processor, embedded, 'cpu')
    assert expected.keys() == actual.keys()
    for key in expected:
        assert torch.equal(expected[key], actual[key]), key
    assert meta['prompt_token_ids'] == old_meta['prompt_token_ids']
    assert meta['visual_token_indices'] == old_meta['visual_token_indices']
    assert meta['image_grid_thw'] == old_meta['image_grid_thw']
    blue = tmp_path / 'blue.png'
    blue.write_bytes(png('blue'))
    second = image_assets(dict(image_path=str(blue)))[0]
    second['slot'] = 'image_2'
    multiple = dict(embedded, prompt='A: <image 2> B: <image 1>', image_layout='inline_markers',
                    image_assets=embedded['image_assets'] + [second])
    _, multi_meta = prepare_condition(processor, multiple, 'cpu')
    assert multi_meta['image_order'] == ['image_2', 'image_1']
    assert multi_meta['visual_images'][0]['decoded_image_sha256'] == second['decoded_sha256']
    assert len(multi_meta['visual_token_indices']) == sum(len(s['visual_token_indices']) for s in multi_meta['visual_images'])
    absent = dict(multiple, no_image=True, image_assets=[])
    text_batch, text_meta = prepare_condition(processor, absent, 'cpu')
    assert not text_meta['visual_token_indices'] and 'pixel_values' not in text_batch
    assert text_meta['image_grid_thw'] is None


def test_family_groups_merge_shared_images_transitively():
    from scripts.stage7a_bench.freeze_native_images_v2 import family_groups
    rows = [dict(example_id=str(i), family_id=str(i), benchmark='mmmu_pro') for i in range(3)]
    assets = {'0': [{'decoded_sha256': 'a'}], '1': [{'decoded_sha256': 'a'}, {'decoded_sha256': 'b'}],
              '2': [{'decoded_sha256': 'b'}]}
    mapping, groups = family_groups(rows, assets)
    assert len(set(mapping.values())) == 1 and groups == [['0', '1', '2']]


def test_image_runner_cannot_accept_assets_in_no_image_condition():
    from scripts.stage7a_bench.native_images_v2 import validate_rows
    with pytest.raises(ValueError, match='No-image'):
        validate_rows([dict(event_id='bad', prompt='Question', no_image=True,
                            image_assets=[dict(kind='parquet')])])
