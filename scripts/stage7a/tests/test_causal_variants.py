import numpy as np
from PIL import Image
import pytest
from scripts.stage7a import causal_variants
from scripts.stage7a.common import sha
from visual_reasoning.stage6a.stimuli import apply_stress


def test_semantic_cf_keeps_current_target_availability(tmp_path, monkeypatch):
    # Synthetic field edit: strong contrast attenuation must remain applied.
    monkeypatch.setattr(causal_variants, 'OUT', tmp_path)
    assets = tmp_path / 'assets' / 'base'
    assets.mkdir(parents=True)
    pixels = np.full((16, 16, 3), 255, dtype='uint8')
    mask = np.zeros((16, 16), dtype=bool)
    mask[4:8, 4:8] = True
    pixels[mask] = 0
    image = Image.fromarray(pixels)
    edited = pixels.copy()
    edited[mask] = 200
    Image.fromarray(edited).save(assets / 'condition__T_semantic.png')
    Image.fromarray(mask.astype('uint8')*255).save(assets / 'roi_mask__T.png')
    native = assets / 'condition__strong.png'
    apply_stress(image, mask, 'strong').save(native)
    row = dict(base_id='base', condition='strong', fields={'T': {}}, image_path=str(native))
    reviewed_sha = sha(assets / 'condition__T_semantic.png')
    variant, audit = causal_variants.semantic_variant(row, 'T', 'semantic', reviewed_sha)
    result = np.asarray(Image.open(variant['image_path']))
    assert result[mask][0, 0] == round(.12*200 + .88*127)
    assert audit['outside_source_exact']
    with pytest.raises(ValueError, match='erased'):
        causal_variants.semantic_variant({**row, 'condition': 'mask'}, 'T', 'semantic', reviewed_sha)
