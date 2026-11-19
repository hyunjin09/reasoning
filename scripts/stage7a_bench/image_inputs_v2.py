"""Bounded, hash-checked benchmark images; no raw dataset cache is written.

Parquet streaming API: https://arrow.apache.org/docs/python/generated/pyarrow.parquet.ParquetFile.html
Chat API: https://huggingface.co/docs/transformers/model_doc/qwen3_vl
"""
import hashlib
import io
import re
import zipfile
from pathlib import Path

import pyarrow.parquet as pq
from PIL import Image

from scripts.stage7a.common import sha


def parquet_row(path, index, columns):
    """Decode one row at a time in its row group, avoiding whole-shard tables."""
    if index < 0:
        raise ValueError('Negative row index')
    with pq.ParquetFile(path) as parquet:
        remaining = index
        for group in range(parquet.num_row_groups):
            count = parquet.metadata.row_group(group).num_rows
            if remaining >= count:
                remaining -= count
                continue
            for offset, batch in enumerate(parquet.iter_batches(
                    batch_size=1, row_groups=[group], columns=columns, use_threads=False)):
                if offset == remaining:
                    return batch.to_pylist()[0]
    raise IndexError(index)


def payload(asset):
    if asset['kind'] == 'file':
        return Path(asset['path']).read_bytes()
    if asset['kind'] == 'zip':
        with zipfile.ZipFile(asset['path']) as archive:
            return archive.read(asset['member'])
    if asset['kind'] == 'parquet':
        value = parquet_row(asset['path'], asset['row_index'], [asset['column']])[asset['column']]
        if isinstance(value, list):
            value = value[asset['list_index']]
        if not isinstance(value, dict) or not value.get('bytes'):
            raise ValueError('Missing embedded image bytes')
        return value['bytes']
    raise ValueError('Unsupported asset kind: ' + asset['kind'])


def decode(data):
    with Image.open(io.BytesIO(data)) as source:
        return source.convert('RGB')


def describe(asset, data):
    image = decode(data)
    return dict(asset, bytes_sha256=hashlib.sha256(data).hexdigest(),
                decoded_sha256=hashlib.sha256(image.tobytes()).hexdigest(), size=list(image.size))


def image_assets(row):
    assets = []
    if row.get('image_path'):
        asset = dict(kind='file', path=row['image_path'], slot='image_1')
        return [describe(asset, payload(asset))]
    if row.get('image_archive'):
        with zipfile.ZipFile(row['image_archive']) as archive:
            for i, member in enumerate(row['archive_image_members']):
                asset = dict(kind='zip', path=row['image_archive'], member=member, slot=f'image_{i+1}')
                assets.append(describe(asset, archive.read(member)))
        return assets
    columns = row.get('image_columns') or [row['image_column']]
    raw = parquet_row(row['annotation_source'], row['row_index'], columns)
    return describe_embedded(row, raw, columns)


def describe_embedded(row, raw, columns):
    assets = []
    for column in columns:
        values = raw[column] if isinstance(raw[column], list) else [raw[column]]
        for index, value in enumerate(values):
            if value is None:
                continue
            if not value.get('bytes'):
                raise ValueError('Missing embedded image bytes')
            slot = column if row.get('image_columns') else f'image_{len(assets)+1}'
            asset = dict(kind='parquet', path=row['annotation_source'], row_index=row['row_index'],
                         column=column, list_index=index, slot=slot)
            assets.append(describe(asset, value['bytes']))
    if not assets:
        raise ValueError('No valid image assets')
    return assets


def image_assets_many(rows):
    """Stream each parquet once when freezing a cohort; retain only hashes."""
    result, groups = {}, {}
    for row in rows:
        if row.get('image_path') or row.get('image_archive'):
            result[row['example_id']] = image_assets(row)
        else:
            groups.setdefault(row['annotation_source'], []).append(row)
    for path, group in groups.items():
        lookup = {r['row_index']: r for r in group}
        if len(lookup) != len(group):
            raise ValueError('Duplicate parquet row identity')
        columns = group[0].get('image_columns') or [group[0]['image_column']]
        with pq.ParquetFile(path) as parquet:
            for index, batch in enumerate(parquet.iter_batches(batch_size=1, columns=columns, use_threads=False)):
                if index in lookup:
                    row = lookup[index]
                    result[row['example_id']] = describe_embedded(row, batch.to_pylist()[0], columns)
                if index >= max(lookup):
                    break
    if len(result) != len(rows):
        raise ValueError('Incomplete cohort image identities')
    return result


def load_asset(asset):
    data = payload(asset)
    if hashlib.sha256(data).hexdigest() != asset['bytes_sha256']:
        raise ValueError('Image payload hash changed')
    image = decode(data)
    if list(image.size) != asset['size'] or hashlib.sha256(image.tobytes()).hexdigest() != asset['decoded_sha256']:
        raise ValueError('Decoded image changed')
    return image


def user_content(row, images):
    if row.get('no_image'):
        if images or row.get('image_assets') or row.get('image_path'):
            raise ValueError('No-image condition contains images')
        return [{'type': 'text', 'text': row['prompt']}], []
    if not images:
        raise ValueError('Image condition has no images')
    if row.get('image_layout') != 'inline_markers':
        return ([{'type': 'image', 'image': image} for _, image in images]
                + [{'type': 'text', 'text': row['prompt']}]), [slot for slot, _ in images]
    lookup = dict(images)
    content, order, start = [], [], 0
    for match in re.finditer(r'<image\s+(\d+)>', row['prompt']):
        if match.start() > start:
            content.append({'type': 'text', 'text': row['prompt'][start:match.start()]})
        slot = 'image_' + match.group(1)
        if slot not in lookup:
            raise ValueError('Image marker has missing asset: ' + slot)
        content.append({'type': 'image', 'image': lookup[slot]})
        order.append(slot)
        start = match.end()
    if start < len(row['prompt']):
        content.append({'type': 'text', 'text': row['prompt'][start:]})
    if set(order) != set(lookup):
        raise ValueError('Unused image assets in inline prompt')
    return content, order


def prepare_condition(processor, row, device):
    import torch
    from visual_reasoning.stage0.attention import visual_grid_metadata
    from visual_reasoning.stage6a.runtime import prepare_condition as canonical

    if row.get('no_image'):
        user_content(row, [])
        return canonical(processor, row, device)
    if row.get('image_path') and not row.get('image_assets'):
        if sha(row['image_path']) != row['image_sha256']:
            raise ValueError('File image hash changed')
        return canonical(processor, row, device)
    images = [(asset['slot'], load_asset(asset)) for asset in row['image_assets']]
    content, order = user_content(row, images)
    batch = processor.apply_chat_template([{'role': 'user', 'content': content}], tokenize=True,
        add_generation_prompt=True, return_dict=True, return_tensors='pt')
    ids = batch['input_ids'][0]
    visual = (ids == int(processor.image_token_id)).nonzero().flatten().tolist()
    grids = batch['image_grid_thw'].tolist()
    if len(grids) != len(order):
        raise RuntimeError('Image order/grid mismatch')
    segments, offset = [], 0
    lookup = dict(images)
    for slot, grid in zip(order, grids):
        mapping = visual_grid_metadata(grid, merge_size=int(processor.image_processor.merge_size),
                                       patch_size=int(processor.image_processor.patch_size))
        count = mapping['visual_token_count']
        positions = visual[offset:offset + count]
        if len(positions) != count or positions[-1] - positions[0] + 1 != count:
            raise RuntimeError('Image token segment mismatch')
        segments.append(dict(slot=slot, image_grid_thw=grid, visual_mapping=mapping,
            visual_token_indices=positions, image_size=list(lookup[slot].size),
            decoded_image_sha256=hashlib.sha256(lookup[slot].tobytes()).hexdigest()))
        offset += count
    if offset != len(visual):
        raise RuntimeError('Unmapped visual tokens')
    single = segments[0] if len(segments) == 1 else None
    metadata = dict(event_id=row['event_id'], condition=row['condition'], no_image=False,
        prompt=row['prompt'], prompt_token_ids=ids.tolist(), prompt_token_count=len(ids),
        visual_token_indices=visual, image_order=order, visual_images=segments,
        image_assets=row['image_assets'], image_path=None,
        image_grid_thw=single['image_grid_thw'] if single else grids,
        visual_mapping=single['visual_mapping'] if single else None,
        image_size=single['image_size'] if single else None,
        decoded_image_sha256=single['decoded_image_sha256'] if single else None,
        image_state_policy='fresh prepare and generation reset for each condition; no donor cache supplied')
    return {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}, metadata
