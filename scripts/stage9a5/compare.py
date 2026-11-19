"""Paired image-level damage contrasts against the immutable CoT reference."""
import numpy as np
from visual_reasoning.stage9a3.analysis import bootstrap


def paired_contrast(thinking, cot, policy):
    def index(rows):
        out = {}
        for r in rows:
            if r['policy'] not in ('full', policy):
                continue
            key = (r['query_id'], r['policy'])
            assert key not in out, key
            out[key] = r
        return out
    a, b = index(thinking), index(cot)
    assert set(a) == set(b)
    queries = sorted(q for q, p in a if p == 'full')
    images = sorted({a[q, 'full']['image_id'] for q in queries})
    values = []
    for image in images:
        ids = [q for q in queries if a[q, 'full']['image_id'] == image]
        assert len(ids) == 2
        for q in ids:
            assert all(d[q, p]['image_id'] == image for d in (a, b) for p in ('full', policy))
        damage_a = np.mean([float(a[q, 'full']['correct']) - float(a[q, policy]['correct']) for q in ids])
        damage_b = np.mean([float(b[q, 'full']['correct']) - float(b[q, policy]['correct']) for q in ids])
        values.append([damage_a, damage_b, damage_a - damage_b])
    values = np.asarray(values)
    draws = bootstrap(values)
    return dict(policy=policy, n_images=len(images), thinking_damage=float(values[:, 0].mean()),
                cot_damage=float(values[:, 1].mean()), difference=float(values[:, 2].mean()),
                ci95=np.quantile(draws[:, 2], [.025, .975]).tolist(),
                images_more_thinking_damage=int((values[:, 2] > 0).sum()),
                images_less_thinking_damage=int((values[:, 2] < 0).sum()),
                images_equal_damage=int((values[:, 2] == 0).sum()),
                images=images, image_values=values.tolist(), seed=920260927, bootstrap_draws=4000,
                independent_unit='image', weighting='equal image; paired arms and two queries')
