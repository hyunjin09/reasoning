"""Incremental output-only review packets, always after the frozen evidence seal."""
import hashlib
import re
from scripts.stage11b.common import ROOT, load, save, sha, now
from visual_reasoning.stage8b.v2_scoring import extract_answer

evidence = ROOT/'annotations/discovery_evidence_final.json'
assert load(evidence)['sealed']
seen = set()
versions = []
for path in (ROOT/'audit').glob('partial_answer_key_v*.json'):
    versions.append(int(path.stem.rsplit('_v', 1)[1]))
    seen.update(r['task_id'] for r in load(path)['rows'])
version = max(versions, default=0)+1
source = {r['item_id']: r for r in load(ROOT/'stage11b_discovery_manifest_v2.json')['rows']}
rows, keys = [], []
for queue in ['discovery', 'source_feasible']:
    for path in sorted((ROOT/queue/'results').glob('*/result.json')):
        receipt = load(path)
        if receipt['task_id'] in seen or receipt['budget_interrupted']:
            continue
        assert sha(path.parent/'generation.json') == receipt['generation_sha256']
        output = load(path.parent/'generation.json')
        assert len(output['generated_token_ids']) == receipt['tokens']
        text = output['raw_decoded_response']
        options = source[receipt['item_id']]['options']
        ident = hashlib.sha256(('stage11b:extract:'+receipt['task_id']).encode()).hexdigest()[:20]
        rows.append(dict(packet_id=ident, text=text, options=options, normal_eos=receipt['normal_eos'],
            at_length_cap=receipt['at_length_cap'], adapter_proposal=extract_answer(text, options)))
        keys.append(dict(packet_id=ident, task_id=receipt['task_id'], path=str(path)))
rows.sort(key=lambda r: r['packet_id'])
if rows:
    save(ROOT/'packets'/f'partial_answer_review_v{version}.json', dict(at=now(), rows=rows,
        evidence_sha256=sha(evidence), masking='No gold, identity, question, arm or eligibility; prior source exposure disclosed.'))
    save(ROOT/'audit'/f'partial_answer_key_v{version}.json', dict(at=now(), rows=keys))
    print('VERSION', version, 'N', len(rows))
    for r in rows:
        text = r['text']
        print('\nID', r['packet_id'], 'EOS', r['normal_eos'], 'CAP', r['at_length_cap'], 'ADAPTER', r['adapter_proposal'])
        print('CLOSING_TEXT', text[-1500:])
        matches = list(re.finditer(r'(?i)\\boxed\{|final answer|answer\s*(?:is|:) ', text))
        print('MARKERS', len(matches))
        for m in matches[-4:]:
            print('MARKER', m.start(), text[max(0, m.start()-50):m.start()+260].replace('\n', ' '))
        proposal = r['adapter_proposal']
        if proposal.get('span'):
            start, end = proposal['span']
            print('ADAPTER_CONTEXT', text[max(0, start-100):end+180].replace('\n', ' '))
else:
    print('No new valid completed outputs to review')
