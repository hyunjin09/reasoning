"""Bind manually reviewed source packets to existing native claims on CPU.

Packets supply all semantic decisions and pixel rectangles. This command only
checks provenance and compiles literal readouts; it never selects a pilot or
creates source edits. Historical reviews and prepared candidates stay intact.
"""
import argparse
import re

from transformers import AutoTokenizer

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.causal_provenance_v2 import load_native_claim, object_sha, stage_path
from scripts.stage7a_bench.source_value_policy_v2 import numeric_replacement

OUT = ROOT / 'outputs/stage7a_bench_v2'


def compile_packet(packet_path, report_request, output_path):
    packet_path = stage_path(packet_path, 'causal_pilot/selection_reviews')
    packet = read_json(packet_path)
    request = read_json(stage_path(report_request, 'native_screen/report_requests'))
    if (packet['benchmark'] != request['benchmark'] or
            packet.get('causal_or_passive_scores_used') is not False or
            packet.get('status') != 'MANUALLY_VIEWED_SOURCE_AND_PREFIX_PACKET_NOT_COMPILED'):
        raise ValueError('Explicit pre-score source packet and matching native request required')
    runtime = read_json(OUT / 'config/runtime_node02_v3.json')
    tokenizer = AutoTokenizer.from_pretrained(runtime['model_checkpoint'], local_files_only=True)
    policy = OUT / 'config/natural_source_value_policy_v2.json'
    prepared = []
    for item in packet['entries']:
        if item.get('causal_or_passive_scores_used') is not False or not item['native_retrieval_note']:
            raise ValueError('Source/prefix review and absence of score selection required')
        condition = item.get('condition', 'image_present')
        binding = request['bindings'][condition]
        rows = read_jsonl(ROOT / binding['manifest'])
        index, ci = item['native_index'], item['claim_index']
        row = rows[index]
        owners = [owner for owner in binding['runs'] if row['event_id'] in owner['event_ids']]
        if len(owners) != 1:
            raise ValueError('Native event must have one declared owning run')
        owner = owners[0]
        reviews = [r for r in read_jsonl(ROOT / owner['review_path']) if r['event_id'] == row['event_id']]
        if len(reviews) != 1:
            raise ValueError('One full native review is required')
        review = reviews[0]
        claim = review['claims'][ci]
        base = OUT / 'native_screen/generations' / owner['native_run_id'] / 'examples' / row['event_id']
        meta = read_json(base / 'input.json')
        raw = read_json(base / 'generation.json')['raw_decoded_response']
        prefix = raw[:claim['readout_char_start']]
        sheet = stage_path(item['source_sheet']['path'], 'causal_pilot/source_review_sheets')
        if sha(sheet) != item['source_sheet']['sha256']:
            raise ValueError('Viewed source sheet changed')
        sources = {}
        for role, key in [('T', 'target_box'), ('X', 'alternative_box')]:
            boxes = item.get(key+'es')
            if boxes is None:
                boxes = [dict(slot=item.get(role+'_slot', 'image_1'), pixels=item[key])]
            sources[role] = []
            for box in boxes:
                matching = [s for s in meta['visual_images'] if s['slot'] == box['slot']]
                if not matching or any(s['image_size'] != matching[0]['image_size'] for s in matching):
                    raise ValueError('Reviewed source slot missing or ambiguous')
                sources[role].append(dict(slot=box['slot'], source_size=matching[0]['image_size'],
                                          pixels=box['pixels']))
        candidates = item['candidates']
        numeric = all(re.fullmatch(r'[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?', value)
                      for value in candidates.values())
        bounds = dict(lower=None if any(v.startswith('-') for v in candidates.values()) else '0',
                      upper=item.get('numeric_upper'), review_note=item['native_retrieval_note'])
        literal_swap = item.get('literal_source_swap_rule')
        if literal_swap:
            if (numeric or not isinstance(literal_swap, str) or not literal_swap.strip() or
                    candidates['correct'] == candidates['alternative_original'] or
                    candidates['foil'] != candidates['alternative_original'] or
                    candidates['target_semantic'] != candidates['alternative_original'] or
                    candidates['alternative_semantic'] != candidates['correct']):
                raise ValueError('Literal swaps require two distinct independently reviewed source values')
            unit = None
        else:
            unit = '' if numeric else item.get('literal_unit')
            if unit is None or any(unit and not v.endswith(unit) for v in candidates.values()):
                raise ValueError('Nonnumeric packet requires an explicit common literal unit')
            for source, target in [('correct', 'foil'), ('correct', 'target_semantic'),
                                   ('alternative_original', 'alternative_semantic')]:
                original = candidates[source][:-len(unit)] if unit else candidates[source]
                expected = numeric_replacement(original, lower=bounds['lower'], upper=bounds['upper'])+unit
                if candidates[target] != expected:
                    raise ValueError('Packet differs from frozen source-only last-digit rule')
        annotation = dict(status='SOURCE_REVIEWED_UNFROZEN_NO_CONTROL_BANK',
            event_id=row['event_id'], claim_index=ci, native_input_sha256=sha(base / 'input.json'),
            generation_sha256=sha(base / 'generation.json'), tokens_sha256=sha(base / 'tokens.jsonl'),
            semantic_review_sha256=object_sha(review), demanded_source_id=claim['source_id'],
            target_ground_truth=claim['ground_truth'], target_source_status='available',
            source_review_note=item['native_retrieval_note'],
            independently_identified_target_and_alternative=True,
            causal_or_passive_scores_used=False, sources=sources,
            alternative=dict(source_id=item['alternative_source_id'],
                review_note=item['native_retrieval_note'], wrong_claim_matches=(
                    not claim['locally_correct'] and candidates['alternative_original'] == claim['readout'])),
            candidates=candidates, source_domain_review=bounds,
            native_retrieval_demand_review=dict(status='SUPPORTED_BY_NATIVE_CONTEXT',
                prior_same_literal_substring_occurrences=prefix.count(claim['readout']),
                prior_correct_literal_substring_occurrences=prefix.count(candidates['correct']),
                question_provided=claim['question_provided'], prior_same_demanded_source_read=False,
                review_note=item['native_retrieval_note'], causal_or_passive_scores_used=False),
            source_review_packet=dict(path=str(packet_path.relative_to(ROOT)), sha256=sha(packet_path)),
            source_sheet=item['source_sheet'], semantic_counterfactuals_reviewed=False,
            matched_shams_reviewed=False, pilot_selected=False, causal_state=None,
            control_preparation_status='No reviewed bank supplied. Missing controls are unavailable, not null effects.')
        if numeric:
            annotation['source_value_policy'] = dict(path=str(policy.relative_to(ROOT)), sha256=sha(policy))
        elif literal_swap:
            annotation['literal_source_swap_rule'] = literal_swap
        else:
            annotation['literal_unit_candidate_rule'] = dict(unit=unit,
                numeric_rule=dict(path=str(policy.relative_to(ROOT)), sha256=sha(policy)),
                note='Apply frozen source-numeral last-digit rotation and retain the reviewed unit verbatim.')
        name = row['event_id']+f'__e{ci:02d}_completion_v13.json'
        ap = OUT / 'causal_pilot/source_reviews' / name
        write_json(ap, annotation, freeze=True)
        entry = load_native_claim(owner['native_run_id'], binding['manifest'], index,
            owner['review_path'], str(ap.relative_to(ROOT)), ci, tokenizer)
        ep = OUT / 'causal_pilot/prepared_candidates' / name
        write_json(ep, entry, freeze=True)
        prepared.append(dict(id=entry['id'], path=str(ep.relative_to(ROOT)), sha256=sha(ep),
            entry_sha256=object_sha(entry), native_index=index, claim_index=ci,
            source_separation_valid=entry['source_separation_valid'],
            source_token_counts={key:len(value) for key,value in entry['source_groups'].items()},
            orientation_audit=entry['event']['orientation_audit'],
            prior_same_literal_substring_occurrences=prefix.count(claim['readout']),
            native_retrieval_note=item['native_retrieval_note']))
        print(entry['id'], prepared[-1]['source_token_counts'], 'separated='+str(entry['source_separation_valid']), flush=True)
    output_path = stage_path(output_path, 'audit')
    write_json(output_path, dict(status='REVIEWED_PACKET_COMPILED_NOT_PILOT_SELECTED',
        packet=dict(path=str(packet_path.relative_to(ROOT)), sha256=sha(packet_path)),
        implementation_sha256=sha(ROOT / 'scripts/stage7a_bench/compile_reviewed_packet_v13.py'),
        entries=prepared, causal_or_passive_scores_used=False), freeze=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--packet', required=True)
    parser.add_argument('--report-request', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    compile_packet(args.packet, args.report_request, args.output)
