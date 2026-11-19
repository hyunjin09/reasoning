"""Literal answer review without gold or paired-outcome access."""
import argparse
import re
from scripts.stage11c.common import ROOT, load, save, sha, now


def packets(label):
    return load(ROOT/'packets'/f'{label}_answer_review.json')['rows']


def show(label, start, count, tail=1600):
    for index, row in enumerate(packets(label)[start:start+count], start):
        text = row['text']
        body = text.rsplit('</think>', 1)[-1]
        print('\nINDEX', index, 'ID', row['packet_id'], 'EOS', row['normal_eos'], 'CAP', row['at_length_cap'])
        print('OPTIONS', row['options'], 'ADAPTER', row['adapter_proposal'])
        print('BODY_CHARS', len(body), 'TAIL_START', max(0, len(body)-tail))
        print(body[-tail:])
        matches = list(re.finditer(r'(?i)\\boxed\{|final answer|answer\s*(?:is|:) ', text))
        print('FINAL_MARKERS', len(matches))
        for match in matches[-5:]:
            print('MARKER', match.start(), text[max(0, match.start()-70):match.start()+350].replace('\n', ' '))
        proposal = row['adapter_proposal']
        if proposal.get('span'):
            left, right = proposal['span']
            print('ADAPTER_CONTEXT', text[max(0, left-100):right+200].replace('\n', ' '))


def write(label, index, answer, quote, reason, ambiguous=False, alternative=None):
    row = packets(label)[index]
    assert reason
    if answer is not None:
        assert isinstance(answer, str) and answer.strip()
        assert quote and quote in row['text']
    if ambiguous:
        assert alternative is not None or answer is None
    save(ROOT/'audit/answer_drafts'/label/f'{row["packet_id"]}.json', dict(at=now(),
        packet_id=row['packet_id'], reviewer='root', answer=answer, quote=quote, reason=reason,
        ambiguous=ambiguous, alternative=alternative, gold_or_correctness_opened=False))


def seal(label):
    path = ROOT/'packets'/f'{label}_answer_review.json'
    rows = [load(ROOT/'audit/answer_drafts'/label/f'{p["packet_id"]}.json') for p in packets(label)]
    assert all(r['gold_or_correctness_opened'] is False for r in rows)
    save(ROOT/'annotations'/f'{label}_answer_review.json', dict(at=now(), sealed=True,
        packet_sha256=sha(path), gold_or_correctness_opened=False, rows=rows,
        limitation='Root reviewed output-only shuffled packets. Earlier source metadata exposure is disclosed; this is literal extraction, not an independent correctness judge.'))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('label')
    p.add_argument('start', type=int)
    p.add_argument('--count', type=int, default=4)
    p.add_argument('--tail', type=int, default=1600)
    a = p.parse_args()
    show(a.label, a.start, a.count, a.tail)
