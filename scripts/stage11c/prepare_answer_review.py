"""Output-only literal answer packets; source evidence must already be sealed."""
import argparse
import hashlib
from scripts.stage11c.common import ROOT, SEED, load, save, sha, now
from visual_reasoning.stage8b.v2_scoring import extract_answer


def main(manifest_name, label, start_family=None, family_count=None):
    evidence = ROOT/'stage11c_e_star_sufficiency_review.json'
    assert load(evidence)['frozen'] and load(evidence)['model_outcomes_opened'] is False
    split = load(ROOT/'stage11c_primary_split.json')
    source = {r['item_id']: r for r in split['primary']+split['reserve']}
    path = ROOT/manifest_name
    manifest = load(path)
    packets, keys = [], []
    tasks = [r for s in manifest['shards'] for r in s['rows']]
    if start_family is not None:
        assert manifest['queue'] == 'native_early' and family_count == 4
        assert start_family in [0, 4, 8, 12]
        tasks = [r for r in tasks if start_family <= r['primary_order'] < start_family+family_count]
        assert len(tasks) == 8
    else:
        assert family_count is None
    for task in tasks:
        dest = ROOT/manifest['queue']/'results'/task['task_id']
        receipt = load(dest/'result.json')
        assert receipt['manifest_sha256'] == sha(path) and not receipt['budget_interrupted']
        assert receipt['generation_sha256'] == sha(dest/'generation.json')
        output = load(dest/'generation.json')
        assert len(output['generated_token_ids']) == receipt['tokens']
        text = output['raw_decoded_response']
        options = source[task['item_id']]['options']
        ident = hashlib.sha256(f'stage11c:{SEED}:extract:{task["task_id"]}'.encode()).hexdigest()[:20]
        packets.append(dict(packet_id=ident, text=text, options=options,
            normal_eos=receipt['normal_eos'], at_length_cap=receipt['at_length_cap'],
            adapter_proposal=extract_answer(text, options)))
        keys.append(dict(packet_id=ident, task_id=task['task_id'], path=str(dest/'result.json')))
    packets.sort(key=lambda r: r['packet_id'])
    save(ROOT/'packets'/f'{label}_answer_review.json', dict(at=now(), rows=packets,
        evidence_sha256=sha(evidence),
        masking='Gold, question, image, item/family/arm identity, eligibility and paired responses omitted; mode may be inferable from text. Prior source exposure must be disclosed.'))
    save(ROOT/'audit'/f'{label}_answer_key.json', dict(at=now(), rows=keys))
    print('ANSWER_PACKETS', label, len(packets), 'NO_GOLD_JOIN')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('manifest_name')
    p.add_argument('label')
    p.add_argument('--start-family', type=int)
    p.add_argument('--family-count', type=int)
    a = p.parse_args()
    main(a.manifest_name, a.label, a.start_family, a.family_count)
