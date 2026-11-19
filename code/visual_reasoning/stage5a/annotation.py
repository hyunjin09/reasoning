"""Semantic annotation validity before any Stage5A causal/passive measurement."""
import hashlib
import json
import re


def canonical_source_class(fact):
    """Normalize already-reviewed ROI kinds; retain original base evidence type."""
    identity=fact['identity'].lower();value=fact['value'].lower()
    if 'marker' in identity or ('right angle' in identity and not fact.get('cf_allowed')):return 'angle_marker'
    if 'tick' in identity:return 'spatial_marker'
    if any(k in identity for k in ('shaded','shading','boundary','extent','quarter sector')):return 'shape_extent'
    if 'coefficient' in identity or 'expression' in identity or any(k in value for k in ('√','π',' + ',' - ')):return 'formula_label'
    if 'gradient' in value or value in ('yellow','orange'):return 'color'
    if re.fullmatch(r'\d+(?:\.\d+)?',value):
        if 'angle' in identity or 'bearing' in identity or ('arc' in identity and 'length' not in identity):return 'angle_label'
        if 'area' in identity:return 'area_label'
        if 'speed' in identity:return 'speed_label'
        return 'length_label'
    if 'number' in identity or value in ('two','three','four','five','six'):return 'spatial_count'
    if value in ('x','y','a','b','h'):return 'symbolic_label'
    return 'spatial_relational'


def semantic_axes(review):
    explicit=review.get('has_explicit_visual_claim',True)
    role=review.get('semantic_role','VISUAL_CLAIM' if explicit else 'CURRENTLY_DEMANDED')
    if role not in ('MENTION_ONLY','CURRENTLY_DEMANDED','VISUAL_CLAIM','VERIFICATION_OR_RECHECK',
                    'REFRESH_OR_REENGAGEMENT','SUBGOAL_TRANSITION','OTHER'):
        raise ValueError('Unknown reviewed semantic role')
    return {'semantic_role':role,'has_explicit_visual_claim':explicit,
            'readout_correctness':review['correctness'],
            'local_correctness':review['correctness'] if explicit else 'NO_EXPLICIT_CLAIM'}


def exact_semantic_candidate(*,tokens,match_start,match_end,counterfactual_value,tokenizer):
    """Keep native history, including byte-carrying tokens at Unicode boundaries."""
    pieces=[str(t['decoded_token']) for t in tokens]
    bounds=[];cursor=0
    for piece in pieces:
        bounds.append((cursor,cursor+len(piece)));cursor+=len(piece)
    if not 0<=match_start<match_end<=cursor:raise ValueError('Invalid native character span')
    first=next(i for i,(a,b) in enumerate(bounds) if a<=match_start<b)
    last=next(i for i,(a,b) in enumerate(bounds) if a<match_end<=b)
    text=''.join(pieces);initial=first
    # Rolling decoded_token can be empty while a token contributes UTF8 bytes.
    # Expand only the native candidate boundary; never retokenize its history.
    while True:
        a=bounds[first][0];b=bounds[last][1]
        original=[int(t['token_id']) for t in tokens[first:last+1]]
        decoded=tokenizer.decode(original,skip_special_tokens=False,clean_up_tokenization_spaces=False)
        if decoded==text[a:b]:break
        if first==0 or initial-first>=16:raise RuntimeError('No complete native UTF8 candidate boundary within16 tokens')
        first-=1
    replacement=text[a:match_start]+counterfactual_value+text[match_end:b]
    alternate=[int(v) for v in tokenizer.encode(replacement,add_special_tokens=False)]
    alternate_text=tokenizer.decode(alternate,skip_special_tokens=False,clean_up_tokenization_spaces=False)
    if alternate_text!=replacement:raise RuntimeError('Replacement does not round-trip exactly')
    if not alternate or original==alternate:raise ValueError('Candidate contrast must be nonempty and distinct')
    history=[int(t['token_id']) for t in tokens[:first]]
    return {'ed_generated_index':first,'history_before_ed_token_ids':history,
        'history_before_ed_text':text[:a],
        'history_before_ed_sha256':hashlib.sha256(json.dumps(history,separators=(',',':')).encode('ascii')).hexdigest(),
        'original_divergent_suffix_ids':original,'counterfactual_divergent_suffix_ids':alternate,
        'original_divergent_suffix_text':decoded,'counterfactual_divergent_suffix_text':alternate_text,
        'original_candidate_exact_generated_tokens':True,'prefix_ends_at_token_boundary':True,
        'native_utf8_boundary_lookback_tokens':initial-first}


def eligibility(record,complete,events):
    natural=bool(complete and events and not record.get('candidate_excluded') and not record.get('identity_exclusion_reason'))
    return natural,natural and not bool(record.get('atlas_excluded_reason'))


def cf_eligible(review,fact,alternative,joint_sources):
    if len(set(joint_sources))!=1:return False
    actual=review['readout'];truth=review['truth']
    try:
        float(actual)
        valid=float(truth)==float(fact['value']) and float(alternative)==float(fact['counterfactual'])
    except ValueError:return False
    return bool(fact.get('cf_allowed',False) and valid)


def temporal_annotation(review,prefix):
    annotation=review.get('temporal_review',{})
    unresolved={'temporal_role':'NONE','previous_source':None,'prior_explicit_availability':None,
                'temporal_unresolved':True,'temporal_evidence':'full native source history not verified'}
    if not annotation.get('full_native_prefix_reviewed'):return unresolved
    role=annotation['role'];seen=annotation['prior_explicit_availability']
    previous=annotation.get('previous_source');quote=annotation.get('evidence_quote','')
    if role not in ('FIRST_USE','REUSE_WITHOUT_INTERVENING_SOURCE','REFRESH_AFTER_OTHER_SOURCE','NONE'):
        raise ValueError('Invalid reviewed temporal role')
    if role=='FIRST_USE' and seen:raise ValueError('First use cannot have reviewed previous use')
    if role in ('REUSE_WITHOUT_INTERVENING_SOURCE','REFRESH_AFTER_OTHER_SOURCE'):
        if not seen or not quote or quote not in prefix:raise ValueError('Reuse requires reviewed prior-source evidence')
    if role=='REFRESH_AFTER_OTHER_SOURCE' and (not previous or previous==review['source']):
        raise ValueError('Refresh requires a different verified previous source')
    return {'temporal_role':role,'previous_source':previous,'prior_explicit_availability':seen,
            'temporal_unresolved':False,'temporal_evidence':annotation}
