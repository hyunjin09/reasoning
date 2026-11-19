"""Join sealed literal extractions to gold while preserving unexecuted rows."""
from pathlib import Path
from scripts.stage11c.common import ROOT, ARMS, load, save, sha, now
from visual_reasoning.stage8b.v2_scoring import equivalent


def grade_literal(answer, source):
    if answer is None:
        return dict(correct=False, answer_status='NO_COMMITTED_FINAL')
    options = source['options']
    if options:
        letters = [chr(65+i) for i in range(len(options))]
        letter = answer.strip().strip('().').upper()
        if letter not in letters:
            matches = [letters[i] for i, option in enumerate(options)
                       if equivalent(answer, option) is True]
            letter = matches[0] if len(matches) == 1 else None
        result = letter == source['answer'] if letter is not None else None
    else:
        result = equivalent(answer, source['answer'])
    return dict(correct=result, answer_status='SCORED' if result is not None else 'UNSCORABLE_LITERAL')


def assemble(manifest_name, label):
    manifest_path = ROOT/manifest_name
    manifest = load(manifest_path)
    split = load(ROOT/'stage11c_primary_split.json')
    annotation_path = ROOT/'annotations'/f'{label}_answer_review.json'
    review = load(annotation_path)
    packet_path = ROOT/'packets'/f'{label}_answer_review.json'
    assert review['sealed'] and review['gold_or_correctness_opened'] is False
    assert review['packet_sha256'] == sha(packet_path)
    keys = load(ROOT/'audit'/f'{label}_answer_key.json')['rows']
    packets = {r['packet_id']: r for r in load(packet_path)['rows']}
    annotations = {r['packet_id']: r for r in review['rows']}
    assert len(annotations) == len(review['rows']) == len(keys) == len(packets)
    assert set(annotations) == set(packets) == {r['packet_id'] for r in keys}
    by_task = {r['task_id']: annotations[r['packet_id']] for r in keys}
    tasks = {r['task_id']: r for s in manifest['shards'] for r in s['rows']}
    assert set(by_task) == set(tasks)
    rows = []
    for source in split['primary']:
        for arm in ARMS:
            ident = f'native_{arm}_{source["item_id"]}'
            base = dict(task_id=ident, item_id=source['item_id'], family_id=source['family_id'],
                arm=arm, condition='native', subject=source['subject'], level=source['level'],
                evidence_type=source['evidence_type'], status='NOT_RUN', correct=None,
                literal_answer=None, answer_status='NOT_RUN', at_length_cap=None,
                normal_eos=None, structural_complete=None, generated_tokens=None,
                ambiguous_extraction=None, alternative_answer=None, alternative_correct=None,
                receipt_path=None, receipt_sha256=None, answer_review_sha256=sha(annotation_path))
            if ident in tasks:
                rpath = ROOT/manifest['queue']/'results'/ident/'result.json'
                receipt = load(rpath)
                assert not receipt['budget_interrupted'] and receipt['manifest_sha256'] == sha(manifest_path)
                assert receipt['task_id'] == ident and receipt['item_id'] == source['item_id']
                assert receipt['family_id'] == source['family_id'] and receipt['arm'] == arm
                assert receipt['generation_sha256'] == sha(rpath.parent/'generation.json')
                assert receipt['input_sha256'] == sha(rpath.parent/'input.json')
                assert receipt['config_sha256'] == sha(ROOT/'config.json')
                annotation = by_task[ident]
                assert annotation['gold_or_correctness_opened'] is False
                packet = packets[annotation['packet_id']]
                assert packet['text'] == load(rpath.parent/'generation.json')['raw_decoded_response']
                if annotation['answer'] is not None:
                    assert annotation['quote'] and annotation['quote'] in packet['text']
                graded = grade_literal(annotation['answer'], source)
                alternative = annotation['alternative']
                base.update(status='COMPLETE', literal_answer=annotation['answer'], **graded,
                    at_length_cap=receipt['at_length_cap'], normal_eos=receipt['normal_eos'],
                    structural_complete=receipt['structural_complete'], generated_tokens=receipt['tokens'],
                    ambiguous_extraction=annotation['ambiguous'], alternative_answer=alternative,
                    alternative_correct=grade_literal(alternative, source)['correct'] if alternative is not None else None,
                    receipt_path=str(rpath), receipt_sha256=sha(rpath))
            rows.append(base)
    assert len(rows) == 2*split['primary_n']
    assert len({(r['family_id'], r['arm']) for r in rows}) == len(rows)
    return rows
