"""Validate fresh native control reviews before the inherited convergence gate.

Fixed-prefix scores and ordinary paired benchmark reviews cannot supply this
evidence. Every condition retains its own complete generated text, input,
tokens and manual same-demand review. Missing or negative evidence stays so.
"""
from scripts.stage7a.annotation_helpers import normalized_value, readout_offset
from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha
from scripts.stage7a_bench.causal_provenance_v2 import object_sha, stage_path
from scripts.stage7a_bench.prior_controls_v10 import load_prior_controls, verify_fixed_input

CONDITIONS = ('mask', 'unrelated', 'no_image')


def review_condition(entry, generation, tokens, meta, result, review, hashes):
    if (review.get('status') != 'MANUALLY_REVIEWED_FULL_NATIVE_CONTROL' or
            review.get('entry_id') != entry['id'] or
            review.get('full_native_text_reviewed') is not True or
            review.get('causal_or_passive_scores_used') is not False or
            any(not isinstance(review.get(k), str) or not review[k].strip()
                for k in ('behavior', 'notes'))):
        raise ValueError('Explicit full native-control review before causal/passive scores is required')
    raw = generation['raw_decoded_response']
    length = meta['prompt_token_count']
    if (length != len(meta['prompt_token_ids']) or
            raw != ''.join(t['decoded_token'] for t in tokens) or
            generation['generated_token_ids'] != [t['token_id'] for t in tokens] or
            generation['generated_token_count'] != len(tokens) or
            result['token_count'] != len(tokens) or
            any(t['token_index'] != i or t['generation_position'] != length+i
                for i, t in enumerate(tokens))):
        raise ValueError('Fresh native text, IDs, counts or positions disagree')
    if (any(review.get(k+'_sha256') != hashes[k] for k in ('generation', 'tokens', 'input', 'result')) or
            any(result.get(k+'_sha256') != hashes[k] for k in ('generation', 'tokens'))):
        raise ValueError('Native control review/result artifact hash mismatch')
    claims = review.get('claims')
    if not isinstance(claims, list):
        raise ValueError('Explicit reviewed claims, including an empty list, are required')
    selected = []
    for claim in claims:
        quote, value = claim.get('quote'), claim.get('readout')
        if (not isinstance(quote, str) or not quote or raw.count(quote) != 1 or
                not isinstance(value, str) or not value or value not in quote):
            raise ValueError('Reviewed control claim has no unique exact native span')
        readout_offset(quote, value, claim.get('readout_occurrence'))
        if claim.get('kind') == 'primary' and claim.get('demand') == 'singleton':
            selected.append(claim)
    expected = normalized_value(entry['reviewed_claim']['readout'])
    # The inherited ASCII text normalizer maps some distinct Unicode-only
    # literals to an empty key. That key supplies no identifiable value.
    identifiable = expected != ('text', '')
    surface_safe = (len(selected) == 1 and
        (entry['reviewed_claim']['readout'].isascii() and selected[0]['readout'].isascii() or
         entry['reviewed_claim']['readout'] == selected[0]['readout']))
    valid = (result.get('complete') is True and result.get('truncated') is False and
        identifiable and surface_safe and len(selected) == 1 and
        normalized_value(selected[0]['readout']) == expected and
        selected[0].get('source_id') == entry['physical_demanded_source'] and
        all(selected[0].get(k) is False for k in
            ('question_provided', 'conditional', 'arithmetic_result')) and
        all(selected[0].get(k) is True for k in
            ('actual_visual_evidence_assertion', 'same_requested_evidence')))
    return dict(valid=bool(valid), behavior=review['behavior'],
        readouts=[c['readout'] for c in selected], complete=result['complete'],
        truncated=result['truncated'], full_native_text_reviewed=True,
        review_sha256=object_sha(review), artifact_sha256=hashes,
        reason='All completed same-demand primary singleton evidence criteria passed' if valid else
               'Incomplete generation, missing/ambiguous claim, different value/source, or nonasserted evidence')


def compile_convergence(entry, conditions):
    if set(conditions) - set(CONDITIONS):
        raise ValueError('Unexpected native availability condition')
    ledger = {c:conditions.get(c, dict(valid=False, reason='Native generation/review unavailable'))
              for c in CONDITIONS}
    return dict(entry_id=entry['id'], available=set(conditions) == set(CONDITIONS),
        converges=all(r.get('valid') is True for r in ledger.values()), conditions=ledger,
        rule='Same explicit demanded-source native evidence under mask, unrelated image and no image; '
             'abstention, hypothetical values and demand-task mismatch do not count',
        fixed_prefix_scores_used=False, causal_state=None)


def load_native_convergence(entry, reference=None):
    if reference is None:
        return compile_convergence(entry, {})
    if entry.get('causal_pilot_frozen') is not True:
        raise ValueError('Native control evidence requires a frozen pilot entry')
    path = stage_path(reference['path'], 'causal_pilot/native_control_reviews')
    if sha(path) != reference['sha256']:
        raise ValueError('Native convergence review changed')
    packet = read_json(path)
    if (packet.get('entry_id') != entry['id'] or
            packet.get('status') != 'REVIEWED_NATIVE_CONTROL_BANK' or
            packet.get('causal_or_passive_scores_used') is not False):
        raise ValueError('Convergence packet differs from frozen entry or uses causal scores')
    run = stage_path(packet['run_directory'], 'causal_pilot/native_controls')
    signature = read_json(run / 'signature.json')
    summary = read_json(run / 'run_summary.json')
    if (sha(run / 'signature.json') != packet['signature_sha256'] or
            sha(run / 'run_summary.json') != packet['summary_sha256'] or
            signature.get('mode') != 'native_controls' or summary.get('mode') != 'native_controls' or
            summary.get('completed') is not True or
            signature.get('entry_sha256', {}).get(entry['id']) != object_sha(entry)):
        raise ValueError('Native-control run is incomplete or differs from frozen entry')
    config_path = ROOT / 'outputs/stage7a_bench_v2/config/runtime_node02_v3.json'
    config = read_json(config_path)
    environment = read_json(run / 'environment.json')
    wrapper = read_json(stage_path(run.parent.parent / 'wrappers' / (run.name+'.json'),
                                   'causal_pilot/wrappers'))
    if (signature.get('generation_protocol') != config['locked_generation_protocol'] or
            signature.get('execution_signature', {}).get('runtime_sha256') != sha(config_path) or
            environment.get('parameter_dtype') != 'torch.bfloat16' or
            environment.get('slurm_job_id') != config['runtime']['slurm_allocation'] or
            wrapper.get('completed') is not True or wrapper.get('exit_code') != 0 or
            wrapper.get('slurm_job_id') != config['runtime']['slurm_allocation']):
        raise ValueError('Native-control runtime, protocol or wrapper completion differs')
    certificate_ref = signature['mechanics_certificate']
    certificate_path = stage_path(certificate_ref['path'], 'causal_pilot/mechanics')
    certificate = read_json(certificate_path)
    if (sha(certificate_path) != certificate_ref['sha256'] or
            certificate.get('status') != 'PASS_ACTUAL_4B_CAUSAL_MECHANICS' or
            certificate.get('execution_signature') != signature['execution_signature']):
        raise ValueError('Native controls lack the exact actual4B mechanics certificate')
    variants, provenance = load_prior_controls(entry)
    if (set(variants) != {'fixed_'+c for c in CONDITIONS} or
            signature.get('control_provenance', {}).get(entry['id']) != provenance or
            signature.get('control_rows', {}).get(entry['id']) != variants):
        raise ValueError('Native controls differ from the frozen reviewed image bank')
    if set(packet.get('conditions', {})) != set(CONDITIONS):
        raise ValueError('Review packet must account for all three native conditions')
    ledger = {}
    for condition in CONDITIONS:
        variant = variants['fixed_'+condition]
        dest = stage_path(run / 'examples' / entry['id'] / condition, 'causal_pilot/native_controls')
        if read_json(dest / 'manifest_row.json') != variant:
            raise ValueError('Fresh native control row was changed')
        meta, result = (read_json(dest / (k+'.json')) for k in ('input', 'result'))
        if (any(result.get(k) != variant[k] for k in ('event_id', 'condition')) or
                result.get('entry_id') != entry['id']):
            raise ValueError('Fresh native control result identity differs')
        verify_fixed_input(entry, entry['native_input'], variant, meta)
        hashes = {k:sha(dest / (k+('.jsonl' if k == 'tokens' else '.json')))
                  for k in ('generation', 'tokens', 'input', 'result')}
        completed = [r for r in summary['results']
                     if r['entry_id'] == entry['id'] and r['condition'] == condition]
        if len(completed) != 1 or completed[0]['result_sha256'] != hashes['result']:
            raise ValueError('Native-control summary does not cover this exact result')
        ledger[condition] = review_condition(entry, read_json(dest / 'generation.json'),
            read_jsonl(dest / 'tokens.jsonl'), meta, result, packet['conditions'][condition], hashes)
    evidence = compile_convergence(entry, ledger)
    evidence.update(review_packet_sha256=sha(path), signature_sha256=packet['signature_sha256'],
                    summary_sha256=packet['summary_sha256'],
                    environment_sha256=sha(run / 'environment.json'))
    return evidence
