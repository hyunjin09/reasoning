"""Freeze Block3B membership and masked native-reasoning packets."""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from visual_reasoning.stage8b.block1_data import digest, save

ROOT = Path('outputs/stage8b_block3b/v1')
B0 = Path('outputs/stage8b_block0/v1')
B2 = Path('outputs/stage8b_block2/v1')


def main():
    hashes = {}
    for stage in ['block0','block1','block2']:
        p = Path(f'outputs/stage8b_{stage}/v1/stage8b_{stage}_freeze.json')
        d = json.loads(p.read_text()); hashes[str(p)] = digest(p)
        for name, expected in {**d['artifacts_sha256'], **d['supporting_sha256']}.items():
            if name not in hashes:
                hashes[name] = digest(name)
            assert hashes[name] == expected, name
    print('upstream_verified',len(hashes),flush=True)
    seal = json.loads((B2/'annotations/semantic_seal.json').read_text())
    cohort = json.loads((B0/'stage8b_block0_cohort_manifest.json').read_text())['rows']
    rows = [r for r in seal['records'] if r['semantic'] == 'T']
    assert len(cohort) == 256 and len(seal['records']) == 456 and len(rows) == 148
    assert Counter(r['local'] for r in rows) == {'L+':120, 'L-':17, 'L?':11}
    packets = {}; anchors = []; original_ids = []
    for item in dict.fromkeys(r['item_id'] for r in rows):
        old = json.loads((B2/f'annotations/packets/{item}.json').read_text())
        pieces = [json.loads(line)['decoded_token'] for line in Path(old['token_file']).read_text().splitlines()]
        assert digest(old['token_file']) == old['token_sha256']
        length = old['reasoning_tokens']; text = ''.join(pieces[:length])
        ends = np.cumsum([len(p) for p in pieces[:length]]).tolist()
        item_anchors = []
        for source in [r for r in rows if r['item_id'] == item]:
            row = dict(source)
            assert text[row['claim_char_start']:row['claim_char_end']] == row['quoted_native_text']
            row.update(t0=row['claim_end_token']-1,tR=row['start_token'],
                       analysis_family_id='alias_mathvision_1707_1245' if item in ['1707','1245'] else row['family_id'],
                       reasoning_tokens=length, packet=str(ROOT/f'annotations/packets/{item}.json'))
            assert 0 <= row['t0'] < length
            anchors.append(row); item_anchors.append(row); original_ids.append(row['event_id'])
        packet = dict(item_id=item, image=old['image'], image_sha256=old['image_sha256'],
            question=old['question'], subject=old['subject'], reasoning_tokens=length,
            token_file=old['token_file'], token_sha256=old['token_sha256'],
            reasoning_text=text, token_char_ends=ends, anchors=item_anchors,
            hidden=['benchmark answer','final correctness','post-think final section','passive features','routing values'])
        dest = ROOT/f'annotations/packets/{item}.json'; save(dest,packet); packets[str(dest)]=digest(dest)
    anchors.sort(key=lambda r:r['review_order'])
    assert [r['event_id'] for r in anchors] == [r['event_id'] for r in rows]
    save(ROOT/'annotations/anchors.json',dict(rows=anchors))
    paths=['plan/stage8b_block3b_post_read_recovery_wandering_plan.md',
           'plan/stage8b_block3b_execution_protocol_v1.md',
           'plan/stage8b_block3a_family_clarification_v1.md',
           'outputs/stage8b_block3a/v1/annotations/image_crosscheck.json',__file__]
    hashes.update({p:digest(p) for p in paths})
    lengths = [r['reasoning_tokens']-r['t0']-1 for r in anchors]
    summary = dict(at=datetime.now(timezone.utc).isoformat(), items=256, original_reviews=456,
        anchors=148, anchor_items=len(packets), local=dict(Counter(r['local'] for r in anchors)),
        original_families=len({r['family_id'] for r in anchors}),
        analysis_families=len({r['analysis_family_id'] for r in anchors}),
        remaining_reasoning_tokens_across_anchors=sum(lengths),
        remaining_length_quartiles=np.quantile(lengths,[0,.25,.5,.75,1]).tolist(),
        masked_packets_sha256=packets, source_sha256=hashes,
        anchors_sha256=digest(ROOT/'annotations/anchors.json'),
        correctness_or_passive_contrasts_opened=False, annotation_complete=False,
        statistical_seed=820260922, bootstrap_draws=4000,
        primary_metrics=['mutation','refresh_compliance128','reretrieval128','delta_tortuosity256'])
    save(ROOT/'audit/preparation_freeze.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ['masked_packets_sha256','source_sha256']},indent=2))


if __name__ == '__main__':
    main()
