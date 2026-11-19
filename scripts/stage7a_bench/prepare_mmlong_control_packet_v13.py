"""Compile explicitly reviewed first-read anchors into versioned review copies.

The input specs are manual decisions, not a candidate-mining algorithm. Native
reviews, report and source responses remain immutable.
"""
from copy import deepcopy
import re

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.source_value_policy_v2 import numeric_replacement

OUT = ROOT / 'outputs/stage7a_bench_v2'


def main():
    specs_path = OUT / 'causal_pilot/selection_reviews/mmlong_manual_source_specs_controls_v12.json'
    specs = read_json(specs_path)
    old_request = OUT / 'native_screen/report_requests/mmlong_pilot_source_refinements_v11.json'
    request = read_json(old_request)
    binding = request['bindings']['image_present']
    rows = read_jsonl(ROOT / binding['manifest'])
    files, changes, entries = {}, [], []
    for spec in specs['entries']:
        index = spec['native_index']
        row = rows[index]
        owner = next(o for o in binding['runs'] if row['event_id'] in o['event_ids'])
        review_path = owner['review_path']
        reviews = files.setdefault(review_path, read_jsonl(ROOT / review_path))
        review = next(r for r in reviews if r['event_id'] == row['event_id'])
        old_ci = spec['old_claim_index']
        old = review['claims'][old_ci]
        raw = read_json(OUT / 'native_screen/generations' / owner['native_run_id'] /
                        'examples' / row['event_id'] / 'generation.json')['raw_decoded_response']
        literal = spec['readout']
        if spec.get('anchor_after'):
            anchor = raw.index(spec['anchor_after'])
            pos = anchor + spec['anchor_after'].rindex(literal)
        else:
            pos = raw.index(literal)
        assert raw[pos:pos+len(literal)] == literal
        ci = old_ci
        if (old['readout_char_start'] != pos or old['readout'] != literal or
                old['ground_truth'] != spec['correct']):
            claim = deepcopy(old)
            start, end = raw.rfind('\n', 0, pos)+1, raw.find('\n', pos)
            if end < 0:
                end = len(raw)
            claim.update(quote=raw[start:end], readout=literal, ground_truth=spec['correct'],
                         char_start=start, char_end=end, readout_char_start=pos,
                         readout_char_end=pos+len(literal))
            claim['readout_occurrence'] = raw[start:pos].count(literal)+1
            ci = len(review['claims'])
            review['claims'].append(claim)
        assert review['claims'][ci]['locally_correct'] is True
        from scripts.stage7a_bench.image_semantic_reviews_v2 import validate_judgment
        judgment = {k:v for k,v in review.items() if k not in ('causal_state','eligible_causal_event','manifest_sha256','generation_sha256')}
        assert validate_judgment(judgment, raw)['claims'] == review['claims']
        prefix = raw[:pos]
        changes.append(dict(native_index=index, old_claim_index=old_ci, claim_index=ci,
            old_offset=old['readout_char_start'], new_offset=pos, quote=review['claims'][ci]['quote'],
            readout=literal, prior_literal_count=prefix.count(literal),
            prior_casefold_literal_count=prefix.casefold().count(literal.casefold()),
            prior_context=prefix[-500:], review_note=spec['note']))
        target, alternative = spec['correct'], spec['X']
        unit = '%' if target.endswith('%') and alternative.endswith('%') else ''
        numeric = all(re.fullmatch(r'[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?',
                                  s[:-1] if unit else s) for s in (target, alternative))
        if numeric:
            values = [numeric_replacement(s[:-1] if unit else s, lower='0',
                                          upper='100' if unit else None)+unit
                      for s in (target, alternative)]
        else:
            values = [alternative, target]
        tp, xp = spec['T_page'], spec['X_page']
        sheet = OUT / f'causal_pilot/source_review_sheets/mmlong_completion_20260915/native_{index:03}_physical_{tp:03}.png'
        alt_sheet = OUT / f'causal_pilot/source_review_sheets/mmlong_completion_20260915/native_{index:03}_physical_{xp:03}.png'
        entry = dict(native_index=index, claim_index=ci, target_box=spec['target_box'],
            alternative_box=spec['alternative_box'], T_slot=f'page_{tp}', X_slot=f'page_{xp}',
            alternative_source_id=spec['alternative_source_id'],
            candidates=dict(correct=target, foil=values[0], target_semantic=values[0],
                alternative_original=alternative, alternative_semantic=values[1]),
            native_retrieval_note=spec['note'],
            source_sheet=dict(path=str(sheet.relative_to(ROOT)), sha256=sha(sheet)),
            alternative_source_sheet=dict(path=str(alt_sheet.relative_to(ROOT)), sha256=sha(alt_sheet)),
            causal_or_passive_scores_used=False)
        if unit:
            entry.update(literal_unit=unit, numeric_upper='100')
        elif not numeric:
            entry['literal_source_swap_rule'] = 'Use the two manually viewed literal source identities as each other\'s readout contrast; no semantic edit validity is implied.'
        entries.append(entry)
    for old_path, reviews in files.items():
        original = ROOT / old_path
        new_path = original.with_name(original.stem+'_pilot_anchors_v13.jsonl')
        if new_path.exists():
            raise FileExistsError(new_path)
        import json
        new_path.write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in reviews))
        for owner in binding['runs']:
            if owner['review_path'] == old_path:
                owner['review_path'] = str(new_path.relative_to(ROOT))
    request_path = OUT / 'native_screen/report_requests/mmlong_pilot_source_refinements_v13.json'
    write_json(request_path, request, freeze=True)
    packet_path = OUT / 'causal_pilot/selection_reviews/mmlong_completion_source_packet02_controls_v13.json'
    write_json(packet_path, dict(status='MANUALLY_VIEWED_SOURCE_AND_PREFIX_PACKET_NOT_COMPILED',
        benchmark='mmlongbench_doc', entries=entries, causal_or_passive_scores_used=False,
        manual_source_specs=dict(path=str(specs_path.relative_to(ROOT)), sha256=sha(specs_path))), freeze=True)
    write_json(OUT / 'audit/mmlong_control_first_read_refinements_v13.json', dict(
        status='VERSIONED_PILOT_ANCHORS_PRESERVE_ORIGINAL_NATIVE_REPORT', entries=changes,
        original_request_sha256=sha(old_request), new_request_sha256=sha(request_path),
        packet_sha256=sha(packet_path), causal_or_passive_scores_used=False), freeze=True)
    for change in changes:
        print(change['native_index'], change['old_claim_index'], '->', change['claim_index'],
              'offset', change['new_offset'], 'prior_casefold', change['prior_casefold_literal_count'])


if __name__ == '__main__':
    main()
