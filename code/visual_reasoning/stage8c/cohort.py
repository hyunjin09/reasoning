"""Input-only conservative family grouping and proportional sampling."""
import hashlib
import re
from collections import Counter, defaultdict

import numpy as np
from PIL import Image
from scipy.fft import dctn


def image_signature(path):
    with Image.open(path) as im:
        im = im.convert('RGB')
        rgb = np.asarray(im)
        exact = hashlib.sha256(str(im.size).encode() + rgb.tobytes()).hexdigest()
        gray = im.convert('L')
        ink = np.asarray(gray) < 245
        yy, xx = np.nonzero(ink)
        if len(xx):
            gray = gray.crop((int(xx.min()), int(yy.min()), int(xx.max())+1, int(yy.max())+1))
        small = np.asarray(gray.resize((32, 32), Image.Resampling.LANCZOS), dtype=float)
        dct = dctn(small, type=2, norm='ortho')[:8, :8].flatten()[1:]
        bits = dct > np.median(dct)
        perceptual = sum(int(b) << i for i, b in enumerate(bits))
        # Trimming + binarized normalized raster captures rescaled drawings.
        normalized = hashlib.sha256((small < 230).tobytes()).hexdigest()
        return dict(exact=exact, phash=perceptual, normalized=normalized,
                    aspect=gray.width/gray.height)


def family_groups(rows, signatures, known_pairs=()):
    parent = {r['item_id']: r['item_id'] for r in rows}
    edges = []

    def root(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def join(a, b, reason):
        if root(a) != root(b):
            parent[root(b)] = root(a)
        edges.append(dict(a=a, b=b, reason=reason))

    owners = {}
    for row in rows:
        rid = row['item_id']; sig = signatures[rid]
        question = re.sub(r'\d+(?:\.\d+)?', '<num>', row.get('question', '').lower())
        question = re.sub(r'\s+', ' ', question).strip()
        keys = [('exact', sig['exact']), ('normalized', sig['normalized'])]
        if len(question) >= 80:
            keys.append(('specific_numeric_normalized_question', question))
        for key in keys:
            if key in owners:
                join(rid, owners[key], key[0])
            owners[key] = rid
    for a, b in known_pairs:
        if a in parent and b in parent:
            join(a, b, 'known_visual_alias')
    ids = list(parent)
    for i, a in enumerate(ids):
        sa = signatures[a]
        for b in ids[:i]:
            sb = signatures[b]
            distance = (sa['phash'] ^ sb['phash']).bit_count()
            if distance <= 10:
                join(a, b, f'conservative_trimmed_phash_distance_{distance}')
    groups = defaultdict(list)
    for rid in ids:
        groups[root(rid)].append(rid)
    families = {}
    for members in groups.values():
        members = sorted(members)
        fid = 'visual_family_' + hashlib.sha256('|'.join(members).encode()).hexdigest()[:20]
        for rid in members:
            families[rid] = fid
    return families, list(groups.values()), edges


def proportional_sample(rows, n, rng):
    """Largest-remainder allocation across observed subject/level/format strata."""
    if len(rows) < n:
        raise ValueError('Insufficient independent input families')
    strata = defaultdict(list)
    for row in rows:
        strata[(row['subject'], row['level'], row['answer_format'])].append(row)
    keys = sorted(strata)
    exact = {k: n*len(strata[k])/len(rows) for k in keys}
    counts = {k: int(exact[k]) for k in keys}
    tie = {k: rng.random() for k in keys}
    order = sorted(keys, key=lambda k: (-(exact[k]-counts[k]), tie[k]))
    for k in order[:n-sum(counts.values())]:
        counts[k] += 1
    selected = []
    for k in keys:
        local = list(strata[k]); rng.shuffle(local)
        selected.extend(local[:counts[k]])
    rng.shuffle(selected)
    assert len(selected) == n and len({r['family_id'] for r in selected}) == n
    return selected


def distribution(rows):
    return {field: dict(Counter(str(r.get(field)) for r in rows))
            for field in ('subject', 'level', 'answer_format', 'problem_type', 'visual_density')}
