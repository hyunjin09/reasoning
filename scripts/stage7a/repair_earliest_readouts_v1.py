"""One-time, pre-scoring correction to the unchanged earliest-readout rule.

Original review and discovery-freeze bytes are archived before replacement.
This script contains manually reviewed native-text selections, never scores.
"""
import copy
from scripts.stage7a.common import OUT, read_json, write_json, sha
from scripts.stage7a.annotation_helpers import readout_offset, record_binding


def main():
    archive = OUT/'audit/earliest_readout_repair_v1'
    assert not archive.exists(), 'One-time amendment already started'
    for run in ['fresh_mechanics_01', 'discovery_causal_01', 'confirmation_causal_01']:
        assert not (OUT/'raw'/run).exists(), 'Repair must precede fresh causal execution'
    corrections = [
        ('docvqa_16440__aba', 'aba_return', 'So all three values: first is 22, second is 4, third is 22.', 1, {}, []),
        ('pope_113701_train__unrelated', 'primary', 'So the answer should be no.', 1, {}, []),
        ('pope_114941_tie__intact', 'primary', 'So the answer should be no.', 1, {}, []),
        ('pope_430052_surfboard__unrelated', 'primary', 'So the answer is no.', 1, {}, []),
        ('docvqa_16835__aba', 'aba_return', '- Conference and Full Day Tutorial: $2195', 1,
         {'explicit_text_memory_reuse': False}, []),
        ('docvqa_364__aba', 'aba_return', 'So for COTTON DUCK# 4:\n\nBefore rinse: 276', 1,
         {'explicit_text_memory_reuse': False,
          'previous_source_review': 'Outside-bank duck6 After=133 precedes the first explicit scalar Before276 return; sampled T/X/T alone does not identify P=X.'}, ['previous_source']),
        ('docvqa_55466__aba', 'aba_return', 'In the table for B. Research Phase, the Salaries row has 1980 as 2.5 and 1981 as 5.0.', 1,
         {'explicit_text_memory_reuse': False}, []),
        ('docvqa_61616__aba', 'aba_return', "That's the Kahului number, which is 877-7260.", 1,
         {'explicit_text_memory_reuse': False}, []),
        ('docvqa_1986__aba', 'aba_first', '"we\'ve handed you what\'s been marked as Exhibit D2455."', 1, {}, []),
        ('docvqa_5511__aba', 'aba_first', 'The image says: "Tuesday, December 17, 3:00pm".', 1, {}, []),
        ('docvqa_59563__aba', 'aba_first', 'Staff Travel ($8.00)', 1, {}, []),
        ('docvqa_234__strong', 'primary', 'Then the "CAS number" column next to it has "87-44-5".', 1, {}, []),
    ]
    prepared = []
    for eid, kind, quote, occurrence, updates, removals in corrections:
        path = OUT/'annotations/native_reviews'/f'{eid}.json'
        review = read_json(path)
        assert review['full_native_text_reviewed'] and not review['causal_or_passive_scores_used']
        raw = read_json(OUT/'native/native_01/examples'/eid/'generation.json')['raw_decoded_response']
        assert raw.count(quote) == 1, (eid, quote)
        matches = [c for c in review['claims'] if c['kind'] == kind]
        assert len(matches) == 1
        claim = matches[0]
        original = copy.deepcopy(claim)
        left = raw.index(quote)
        start = left + readout_offset(quote, claim['readout'], occurrence)
        assert start < claim['readout_char_start'], eid
        claim.update(quote=quote, char_start=left, char_end=left+len(quote),
                     readout_char_start=start, readout_char_end=start+len(claim['readout']),
                     readout_occurrence=occurrence, **updates)
        for key in removals:
            claim.pop(key, None)
        review['annotation_amendment'] = {
            'id': 'earliest_readout_repair_v1', 'original_review_sha256': sha(path),
            'reason': 'First eligible explicit readout under unchanged frozen event_sampling_rules; before causal or passive scores.'}
        prepared.append((path, review, original, copy.deepcopy(claim)))
    # Preserve every currently available review, not only amended files.
    originals = []
    for directory in ['native_reviews', 'binding_reviews']:
        for path in sorted((OUT/'annotations'/directory).glob('*.json')):
            dest = archive/'original_reviews'/directory/path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(path.read_bytes())
            originals.append(dict(path=str(path), archived_path=str(dest), sha256=sha(path)))
    for relative in ['config/discovery_events.jsonl', 'audit/discovery_events.json',
                     'audit/discovery_semantic_review_summary.json']:
        path = OUT/relative
        dest = archive/'original_freeze'/path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())
        originals.append(dict(path=str(path), archived_path=str(dest), sha256=sha(path)))
    changed = []
    for path, review, before, after in prepared:
        write_json(path, review)
        changed.append(dict(event_id=review['event_id'], split=review['split'],
                            old_claim=before, new_claim=after, new_review_sha256=sha(path)))
    binding_path = OUT/'annotations/binding_reviews/docvqa_234__strong.json'
    assert (archive/'original_reviews/binding_reviews'/binding_path.name).exists()
    binding_path.unlink()
    record_binding('docvqa_234__strong',
        'Scanning through the table, the first entry under "Compound" is Caryophyllene. Then the "CAS number" column next to it has "87-44-5".',
        'Caryophyllene', 'Sclareol', '87-44-5',
        notes='Earliest explicit entity-CAS binding; unchanged literal value, role-only foil. Original later binding archived by earliest_readout_repair_v1 before any scores.')
    for relative in ['config/discovery_events.jsonl', 'audit/discovery_events.json',
                     'audit/discovery_semantic_review_summary.json']:
        (OUT/relative).unlink()  # Exact original bytes preserved above; rebuild canonical freeze next.
    write_json(archive/'amendment.json', dict(
        status='ANNOTATIONS_REPAIRED_AWAITING_MANIFEST_REBUILD',
        changed=changed, originals=originals,
        binding_amendment=dict(event_id='docvqa_234__strong', new_sha256=sha(binding_path)),
        causal_or_passive_scores_used=False, sampling_rules_changed=False,
        exclusions_reconciled={
            'literal_collisions': 'mathvista312 year2003 contains20;627/828/824 repeated literals name other fields. Preserve role identity.',
            'compound_or_tentative': 'mathvista719 temperature list;doc364 mask tentative parses;57307 scalar start versus whole ranges;1986 page/volume;59428 explicit start-day resolution. Keep first unambiguous eligible scalar claim.',
            'binary_grammar': 'Earlier no+noun slots cannot take the frozen yes foil grammatically. Select earliest grammatical yes/no answer slot.',
            'unrealized_return': 'doc7020 third demand resolves to a different blank column; final first-answer recap does not repair the failed third demand.'}), freeze=True)
    print('Archived originals; amended 12 native reviews and 1 binding; rebuild discovery freeze and confirmation snapshot next.')


if __name__ == '__main__':
    main()
