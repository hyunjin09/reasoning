import numpy as np
from PIL import Image
from transformers import AutoProcessor
from scripts.stage7a.common import OUT, read_json, configure_fresh_processor
from scripts.stage7a.run_prepare_cohort import exact_processed_image, source_components, split_sources


def test_actual_processor_patch_inverse_preserves_unresized_pixels():
    config=read_json(OUT/'config/stage7a_config.json')
    processor=AutoProcessor.from_pretrained(config['model_checkpoint'],local_files_only=True)
    configure_fresh_processor(processor)
    rng=np.random.default_rng(732)
    raw=rng.integers(0,256,(256,256,3),dtype=np.uint8)
    batch=processor.image_processor(images=Image.fromarray(raw),return_tensors='pt')
    restored=np.asarray(exact_processed_image(batch,processor))
    assert np.array_equal(raw,restored)


def test_near_image_group_cannot_cross_split():
    rows=[]
    for i,ph in enumerate(['0','1','ffffffffffffffff','fffffffffffffffe','aaaaaaaaaaaaaaaa','5555555555555555']):
        rows.append(dict(base_id=str(i),dataset='test',cohort='C1',identity=dict(width=320,height=320,decoded_stimulus_sha256=str(i),phash=ph)))
    groups,pairs=source_components(rows)
    assignments,_=split_sources(rows,groups)
    assert pairs
    assert assignments['0']['split']==assignments['1']['split']
    assert assignments['2']['split']==assignments['3']['split']
    assert {r['split'] for r in assignments.values()}=={'discovery','confirmation'}
