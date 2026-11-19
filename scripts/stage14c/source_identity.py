"""Source-only family keys. Gold answers and rendered model outputs are not inputs."""
import json
import re


def blind_identity(task, filename, metadata):
    if task == 'Line Plot Intersections':
        match = re.fullmatch(r'gt_\d+_image_(\d+)_thickness_[\d.]+_resolution_\d+\.png', filename)
        if not match: raise ValueError('Missing verified generator base-instance ID')
        key = {'base_instance': int(match[1])}
    elif task.startswith('Counting Grid -'):
        match = re.fullmatch(r'grid_(\d+)x(\d+)_\d+_[\d.]+\.png', filename)
        if not match: raise ValueError('Missing source grid dimensions')
        # Generator fixes word content by row/column; style/resolution do not change it.
        key = {'source_rows': int(match[1]), 'source_columns': int(match[2])}
    elif task == 'Circled Letter':
        key = {k: metadata[k] for k in ('word', 'circle_index')}
    elif task == 'Touching Circles':
        key = {k: metadata[k] for k in ('center_1', 'center_2', 'diameter')}
    elif task.startswith('Olympic Counting -'):
        shape_size = 'diameter' if task.endswith('Circles') else 'side'
        key = {k: metadata[k] for k in ('centers', shape_size)}
    elif task == 'Nested Squares':
        key = {'squares': metadata['squares']}
    elif task == 'Subway Connections':
        key = {'connections': sorted([sorted([r['start'], r['end']]) + [r['color']] for r in metadata['connections']])}
    else:
        raise ValueError('Unsupported task; source review required')
    return task + '|' + json.dumps(key, sort_keys=True, separators=(',', ':'))


def connected_components(ids, edges):
    parent = {i:i for i in ids}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a,b in edges:
        ra,rb = find(a),find(b)
        parent[max(ra,rb)] = min(ra,rb)
    groups = {}
    for i in sorted(ids): groups.setdefault(find(i), []).append(i)
    return sorted(groups.values())
