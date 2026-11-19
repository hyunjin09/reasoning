"""Four independent Slurm ranks: validate cached traces, then GPU geometry."""
import argparse
import json
import os
import socket
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch

from prepare_block0 import ROOT, digest, save
from visual_reasoning.stage8b.block0 import (TAU, Z_KEYS, episodes, phase,
    feature_vectors, geometry, completion, trajectory_metrics, phase_metrics, review_indices)
from visual_reasoning.stage8b.passive import FEATURE_KEYS, frozen_scores
from visual_reasoning.stage8b.transfer import reasoning_length


def check_frozen_sources():
    freeze = json.loads((ROOT/'audit'/'input_freeze.json').read_text())
    for path, expected in freeze['source_sha256'].items():
        assert digest(path) == expected, path
    for path, expected in json.loads((ROOT/'audit'/'execution_source_freeze.json').read_text())['source_sha256'].items():
        assert digest(path) == expected, path
    assert digest(freeze['cohort_manifest']) == freeze['cohort_manifest_sha256']
    assert freeze['detector']['tau_R'] == TAU
    assert digest(freeze['detector']['models']) == freeze['detector']['models_sha256']
    return freeze


def raw_item(row, model, cfg):
    receipt_path = Path(row['receipt'])
    assert digest(receipt_path) == row['receipt_sha256']
    receipt = json.loads(receipt_path.read_text())
    for path, expected in receipt['provenance_sha256'].items():
        assert digest(path) == expected, path
    p = receipt_path.parent
    gen = json.loads((p/'generation.json').read_text())
    inp = json.loads((p/'input.json').read_text())
    tokens = [json.loads(line) for line in (p/'tokens.jsonl').read_text().splitlines()]
    native = json.loads((p/'manifest_row.json').read_text())
    n = len(tokens)
    assert receipt['tokens'] == gen['generated_token_count'] == receipt['observation_rows'] == n
    assert [t['token_index'] for t in tokens] == list(range(n))
    assert [t['token_id'] for t in tokens] == gen['generated_token_ids']
    assert [t['generation_position'] for t in tokens] == list(range(inp['prompt_token_count'], inp['prompt_token_count']+n))
    pieces = [t['decoded_token'] for t in tokens]
    assert ''.join(pieces) == gen['raw_decoded_response']
    assert native['item_id'] == row['item_id'] and native['family_id'] == row['family_id']
    assert native['protocol_id'] == cfg['protocol_id']
    assert gen['model_revision'] == cfg['model_revision']
    for key, value in cfg['generation_parameters'].items():
        assert gen['generation_parameters'][key] == value, key
    assert gen['generation_parameters']['max_new_tokens'] == 40960
    assert gen['seed'] == native['seed'] == 1234
    assert inp['preprocessing']['min_pixels'] == cfg['min_pixels']
    assert inp['preprocessing']['max_pixels'] == cfg['max_pixels']
    assert inp['generation_query'] == native['generation_query']
    assert digest(native['image']) == native['image_sha256']
    length = reasoning_length(pieces)
    assert length > 0
    with np.load(p/'passive.npz') as a:
        f = a['features']; scores = a['retrieval_score']; keys = a['feature_keys'].tolist()
        assert a['visual_positions'].tolist() == inp['visual_token_indices']
    assert keys == FEATURE_KEYS and f.shape == (n, 8) and scores.shape == (n,)
    recomputed = frozen_scores(f, model, keys)
    np.testing.assert_allclose(scores, recomputed, rtol=0, atol=1e-12, equal_nan=True)
    assert np.isnan(scores[0]) and np.isfinite(scores[1:]).all()
    z = feature_vectors(f[:length], scores[:length])
    char_ends = np.cumsum([len(t) for t in pieces])
    table = pd.DataFrame(dict(item_id=row['item_id'], family_id=row['family_id'], order=row['order'],
        token_index=np.arange(length), generation_position=np.arange(length)+inp['prompt_token_count'],
        token_id=gen['generated_token_ids'][:length], char_start=np.r_[0,char_ends[:-1]][:length],
        char_end=char_ends[:length], normalized_position=np.arange(length)/length,
        phase=phase(np.arange(length)/length), R=scores[:length],
        R_valid=np.isfinite(scores[:length]), active_retrieval=scores[:length] > TAU,
        z_valid=np.isfinite(z).all(1)))
    for i, key in enumerate(FEATURE_KEYS):
        table[key] = f[:length, i]
    table['visual_concentration'] = z[:, 3]
    es = {}
    for gap in [0, 4, 8]:
        es[str(gap)] = [dict(e, item_id=row['item_id'], family_id=row['family_id'], order=row['order'],
                            event_id=f"mathvision_{row['item_id']}_gap{gap}_e{e['episode_index']:05d}")
                       for e in episodes(scores[:length], gap)]
        assert es[str(gap)] == [dict(e, item_id=row['item_id'], family_id=row['family_id'], order=row['order'],
                                   event_id=f"mathvision_{row['item_id']}_gap{gap}_e{e['episode_index']:05d}")
                              for e in episodes(scores[:length], gap)]
    for e in es['4']:
        segment = table.iloc[e['start_token']:e['end_token']+1]
        for key in Z_KEYS[1:]:
            e['mean_'+key] = float(segment[key].mean())
    text = gen['raw_decoded_response']
    boundary_end = text.find('</think>') + 8 if '</think>' in text else None
    post = int(np.sum(np.r_[0,char_ends[:-1]] >= boundary_end)) if boundary_end is not None else None
    metrics = trajectory_metrics(scores[:length], es['4'], generated_tokens=n, post_think_tokens=post)
    selected = [es['4'][i]['event_id'] for i in review_indices(es['4'])]
    meta = dict(item_id=row['item_id'], family_id=row['family_id'], order=row['order'],
        completion=completion(receipt, text), metrics=metrics, episodes=es, selected_event_ids=selected,
        source_checks=dict(artifact_hashes=len(receipt['provenance_sha256']), image_hash=True,
            token_alignment=True, generation_metadata=True, detector_R_max_abs_error=float(np.max(np.abs(scores[1:]-recomputed[1:])))),
        roi_structure=dict(image_source_type='MathVision raster image', image_path=native['image'],
            image_sha256=native['image_sha256'], image_size=native['image_size'],
            patch_mapping_available=bool(inp['visual_mapping']), native_replay_inputs_available=True),
        delimiter_tokens=n-length-post if post is not None else 0)
    return table, z, meta


def main(stage):
    rank = int(os.environ['SLURM_PROCID'])
    assert int(os.environ['SLURM_NTASKS']) == 4
    assert socket.gethostname().split('.')[0] == 'node02'
    assert torch.cuda.device_count() == 1
    torch.cuda.set_device(0)
    freeze = check_frozen_sources()
    rows = json.loads((ROOT/'stage8b_block0_cohort_manifest.json').read_text())['rows'][rank::4]
    cfg = json.loads(Path(freeze['canonical_config']).read_text())
    assert cfg['presence_penalty'] == 0
    # BF16 is enforced by the frozen native runner, not a config key.
    for source, expected in cfg['source_sha256'].items():
        assert digest(source) == expected, source
    assert 'assert str(next(model.parameters()).dtype)=="torch.bfloat16"' in Path('scripts/stage8b/run_native_v2.py').read_text()
    dest = ROOT/'workers'/f'rank{rank}'
    dest.mkdir(parents=True, exist_ok=True)
    env = dict(stage=stage, rank=rank, host=socket.gethostname(), slurm_job_id=os.environ['SLURM_JOB_ID'],
               gpu=str(torch.cuda.get_device_properties(0)), gpu_uuid=str(torch.cuda.get_device_properties(0).uuid),
               torch=torch.__version__, numpy=np.__version__, pandas=pd.__version__)
    save(dest/f'{stage}_environment.json', env)
    print(json.dumps(dict(event='worker_start', **env)), flush=True)
    probe = np.array([[np.nan,0.,0.,0.],[0.,0.,0.,0.],[3.,4.,0.,0.],[0.,0.,0.,0.]])
    ref, _ = geometry(probe); actual, _ = geometry(probe, device='cuda:0')
    assert ref == actual
    started = time.monotonic()
    if stage == 'extract':
        model = joblib.load(freeze['detector']['models'])['joint']['model']
        moments = []
    else:
        std = json.loads((ROOT/'audit'/'standardization_freeze.json').read_text())
    for i, row in enumerate(rows):
        clock = time.monotonic()
        out = ROOT/'items'/row['item_id']; out.mkdir(parents=True, exist_ok=True)
        if stage == 'extract':
            table, z, meta = raw_item(row, model, cfg)
            x = torch.as_tensor(z, dtype=torch.float64, device='cuda:0')
            valid = torch.isfinite(x); count = valid.sum(0)
            mean = torch.where(valid, x, 0).sum(0)/count
            m2 = torch.where(valid, (x-mean)**2, 0).sum(0)
            moments.append(dict(item_id=row['item_id'], count=count.cpu().tolist(), mean=mean.cpu().tolist(), m2=m2.cpu().tolist()))
            table.to_parquet(out/'raw.parquet', index=False)
            save(out/'meta.json', meta)
        else:
            table = pd.read_parquet(out/'raw.parquet')
            meta = json.loads((out/'meta.json').read_text())
            raw = table[Z_KEYS].to_numpy(dtype=np.float64)
            x = torch.as_tensor(raw, dtype=torch.float64, device='cuda:0')
            scaled = ((x-torch.tensor(std['mean'],device='cuda:0',dtype=torch.float64))/torch.tensor(std['scale'],device='cuda:0',dtype=torch.float64)).cpu().numpy()
            for j, key in enumerate(Z_KEYS):
                table['standardized_'+key] = scaled[:, j]
            gs, movements = {}, {}
            for name, vector in [('raw', raw), ('standardized', scaled)]:
                gs[name], movements[name] = geometry(vector, device='cuda:0')
                if i == 0:
                    cpu, _ = geometry(vector)
                    for key, value in cpu.items():
                        if value is not None:
                            np.testing.assert_allclose(gs[name][key], value, rtol=1e-11, atol=1e-11)
            save(out/'derived.json', dict(geometry=gs, phases=phase_metrics(table, meta['episodes']['4'], movements)))
            table.to_parquet(out/'features.parquet', index=False)
        record = dict(event='sample_complete', stage=stage, rank=rank, item_id=row['item_id'],
            completed=i+1, target=len(rows), reasoning_tokens=len(table), elapsed_seconds=time.monotonic()-started,
            sample_seconds=time.monotonic()-clock, peak_gpu_bytes=torch.cuda.max_memory_allocated())
        with (dest/f'{stage}_progress.jsonl').open('a') as stream:
            stream.write(json.dumps(record)+'\n')
        print(json.dumps(record), flush=True)
    if stage == 'extract':
        save(dest/'moments.json', moments)
    save(dest/f'{stage}_complete.json', dict(completed=True, items=[r['item_id'] for r in rows],
                                          elapsed_seconds=time.monotonic()-started))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('stage', choices=['extract','geometry'])
    main(ap.parse_args().stage)
