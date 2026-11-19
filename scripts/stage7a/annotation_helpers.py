"""Persist manual, full-native-text semantic review independently of causal scores."""
import re
from decimal import Decimal, InvalidOperation
from scripts.stage7a.common import OUT, read_json, read_jsonl, write_json, sha


def normalized_value(value):
    text=str(value).strip().lower().replace(',','').replace('$','').replace('%','')
    try: return ('number',str(Decimal(text).normalize()))
    except InvalidOperation: return ('text',re.sub(r'[^a-z0-9]','',text))


def readout_offset(quote, readout, occurrence=None):
    positions = [m.start() for m in re.finditer(re.escape(readout), quote)]
    if occurrence is None:
        if len(positions) != 1:
            raise ValueError('Repeated readout requires explicit one-based occurrence')
        occurrence = 1
    if not 1 <= occurrence <= len(positions):
        raise ValueError('Readout occurrence is outside quote')
    return positions[occurrence - 1]


def record_review(event_id, selections, *, behavior, notes, downstream=None, split='discovery', run='native_01'):
    dest=OUT/'native'/run/'examples'/event_id
    result=read_json(dest/'result.json'); row=read_json(dest/'manifest_row.json')
    assert row['split']==split
    if not result['complete']:
        assert not selections and behavior == 'incomplete_generation'
    generation=read_json(dest/'generation.json');tokens=read_jsonl(dest/'tokens.jsonl')
    raw=generation['raw_decoded_response']
    assert raw==''.join(t['decoded_token'] for t in tokens)
    claims=[]
    for selection in selections:
        source,quote,readout,kind=selection[:4]
        assert raw.count(quote)==1,(event_id,quote,raw.count(quote))
        assert readout in quote
        extra=selection[4] if len(selection)>4 else {}
        left=raw.index(quote);offset=readout_offset(quote,readout,extra.get('readout_occurrence'))
        truth=row['fields'][source]['value'] if row['fields'] else ('yes' if row['present'] else 'no')
        claim=dict(source_id=source,quote=quote,char_start=left,char_end=left+len(quote),
            readout=readout,readout_char_start=left+offset,readout_char_end=left+offset+len(readout),
            ground_truth=truth,locally_correct=normalized_value(readout)==normalized_value(truth),
            kind=kind,demand='singleton',semantic_role='explicit_requested_field_claim',
            question_provided=False,conditional=False,arithmetic_result=False,
            local_truth_scope='original reviewed field; original-answer agreement does not establish evidence availability in a mask/unrelated/no-image condition')
        if len(selection)>4: claim.update(selection[4])
        claims.append(claim)
    write_json(OUT/'annotations/native_reviews'/f'{event_id}.json',dict(event_id=event_id,base_id=row['base_id'],
        split=split,condition=row['condition'],behavior=behavior,claims=claims,notes=notes,
        downstream=downstream,full_native_text_reviewed=result['complete'],native_generation_complete=result['complete'],source_image_review='cohort frozen source annotation and pixel review',
        generation_sha256=sha(dest/'generation.json'),tokens_sha256=sha(dest/'tokens.jsonl'),
        causal_or_passive_scores_used=False),freeze=True)


def record_binding(event_id, quote, literal_role, foil_role, value, *, source='T', notes):
    """Manually certified binding contrast; the candidate value stays literal."""
    review = read_json(OUT / 'annotations/native_reviews' / (event_id + '.json'))
    native = OUT / 'native/native_01/examples' / event_id
    raw = read_json(native / 'generation.json')['raw_decoded_response']
    row = read_json(native / 'manifest_row.json')
    assert raw.count(quote) == 1 and quote.count(literal_role) == 1 and quote.count(value) == 1
    assert normalized_value(value) == normalized_value(row['fields'][source]['value'])
    # Keep the value inside both complete candidate suffixes. Candidate history
    # starts at the role, not at a retokenized version of preceding native text.
    start = quote.index(literal_role)
    assert quote.index(value) > start
    actual = quote[start:quote.index(value)+len(value)]
    foil = actual.replace(literal_role, foil_role, 1)
    absolute = raw.index(quote)+start
    claim = dict(source_id=source, quote=quote, readout=actual, readout_char_start=absolute,
                 readout_char_end=absolute+len(actual), ground_truth=actual, locally_correct=True,
                 correct_readout=actual, foil_readout=foil, value_held_fixed=value,
                 kind='binding', readout_type='B', demand='singleton',
                 semantic_role='explicit_entity_value_binding', conditional=False,
                 question_provided=False, arithmetic_result=False, notes=notes)
    write_json(OUT / 'annotations/binding_reviews' / (event_id+'.json'),
               dict(event_id=event_id, claim=claim, generation_sha256=review['generation_sha256'],
                    causal_or_passive_scores_used=False), freeze=True)
