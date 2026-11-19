"""Conservative text-semantic rules; no attention, scores or truth-based selection.

These annotate identifiable requests/claims. Merely matching an entity does not
establish demand, and unmapped reasoning remains explicitly unresolved.
"""
import re

VISUAL_PREDICATE=re.compile(r'\b(?:shows?|shown|label(?:ed|led)?|read|look(?:ing)?|see|visible|given|listed|states?|says|identify|locate|find|need|use|using|plug|substitut\w*|check|verify|confirm)\b',re.I)
ASSERTION=re.compile(r'\b(?:is|are|has|have|equals?|shows?|shown|given|listed|labeled|labelled|says|states?)\b|=',re.I)
HEDGE=re.compile(r'\b(?:maybe|perhaps|probably|might|could|assuming|suppose|if)\b|\?',re.I)
META=re.compile(r'^(?:okay[,.]?\s*)?(?:let me (?:think|calculate|double-check)|i think that(?:\x27s| is) (?:it|correct)|that (?:seems|looks) (?:right|correct)|yes|yep|correct|final answer|step\s*\d+|[-=*#$\s]+)[.!:\s]*$',re.I)


def reviewed_visual_correctness(claims):
    labels=[r['local_visual_correctness'] for r in claims]
    if any(label.startswith('INCORRECT') for label in labels):return 'INCORRECT'
    return 'CORRECT' if labels and all(label=='CORRECT' for label in labels) else 'UNRESOLVED'


def completed_claims(span,claims):
    """Assign a reviewed assertion once, at its completion in native text."""
    return [{**claim,'claim_crosses_span_boundary':claim['char_start']<span['char_start'],
        'span_assignment':'Span containing the end of the reviewed assertion; full claim offsets are retained.'}
        for claim in claims if span['char_start']<claim['char_end']<=span['char_end']]


def classify_span(text,sources,task_sources=(),manual_claim=None):
    mentioned=sorted(key for key,pattern in sources.items() if re.search(pattern,text,re.I))
    if manual_claim is not None:
        return dict(demanded_sources=['T'],mentioned_sources=sorted(set(mentioned)|{'T'}),
            explicit_visual_claim_sources=['T'],unresolved=False,
            semantic_role='REVIEWED_LOCAL_VISUAL_CLAIM',semantic_evidence=manual_claim)
    if META.fullmatch(text.strip()):
        return dict(demanded_sources=[],mentioned_sources=mentioned,explicit_visual_claim_sources=[],
            unresolved=False,semantic_role='NO_EXPLICIT_VISUAL_DEMAND',semantic_evidence='Standalone metacognitive/formatting statement')
    request=bool(VISUAL_PREDICATE.search(text))
    # Digits inside an entity ID (WP2(2), for example) are not a readout.
    claim=bool(re.search(r'(?:\b(?:is|are|equals?|given as|listed as)\s+|=\s*)[\s$*]*(?:[-+]?\d|yes\b|no\b|present\b|absent\b)',text,re.I))
    if mentioned and (request or claim):
        demanded=mentioned
        # A contextual entity in the frozen A-only question is alignment, while
        # the requested field carries demand. Other joint mentions stay unresolved.
        contextual=bool(re.search(r'\b(?:containing|mentions?|includes?)\b',text,re.I))
        if len(mentioned)>1 and contextual and set(task_sources)<=set(mentioned):demanded=sorted(task_sources)
        elif len(mentioned)>1:
            return dict(demanded_sources=[],mentioned_sources=mentioned,explicit_visual_claim_sources=[],
                unresolved=True,semantic_role='UNRESOLVED_JOINT_MENTION',semantic_evidence='Multiple fields mentioned without unambiguous per-field demand')
        # Source names and numeric copulas can also occur in formulas or derived
        # properties (e.g. "surface area is4πr²", "slope ofXY=4/3"). They do not
        # establish acquisition of the localized fact. Prior explicit access is
        # promoted only through a reviewed source-linked native claim override.
        return dict(demanded_sources=demanded,mentioned_sources=mentioned,explicit_visual_claim_sources=[],
            candidate_visual_claim_sources=demanded if claim and not HEDGE.search(text) else [],
            unresolved=False,semantic_role='VISUAL_REQUEST_OR_USE',
            semantic_evidence='Source alias plus request/use predicate; visual fact acquisition requires separate source-linked claim review')
    return dict(demanded_sources=[],mentioned_sources=mentioned,explicit_visual_claim_sources=[],
        unresolved=True,semantic_role='UNRESOLVED',semantic_evidence='Source demand not resolved by conservative semantic rules; mention alone is insufficient')
