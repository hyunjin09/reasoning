"""Join verified manual source judgments to current canonical native claims.

The caller verifies coverage and source-file hashes before calling. This pure
join retains unknowns and does not admit pilots, inspect scores or release work.
"""
from scripts.stage7a_bench.causal_provenance_v2 import object_sha
from scripts.stage7a_bench.mathwild_feasibility_v5 import METRICS


PENDING_LEGACY_STATUS = 'NOT_ADMITTED_PENDING_SEPARATE_READOUT_FRESHNESS_AND_SOURCE_COMPILATION'


def build_ledger(coverage, assessments):
    expected = {(review['event_id'], i): (review, claim)
                for review in coverage['reviews'] for i, claim in enumerate(review['claims'])}
    sources = {}
    for assessment in assessments:
        key = (assessment['event_id'], assessment['claim_index'])
        if key in sources or key not in expected:
            raise ValueError('Duplicate or unreviewed source assessment')
        review, claim = expected[key]
        if (assessment.get('causal_or_passive_scores_used') is not False or
                assessment.get('semantic_review_object_sha256') != object_sha(review) or
                assessment.get('claim_sha256') != object_sha(claim) or
                any(assessment.get(k) != review[k] for k in ('native_index', 'base_id')) or
                any(assessment.get(a) != claim[c] for a, c in
                    (('source_id', 'source_id'), ('emitted_readout', 'readout'),
                     ('source_truth', 'ground_truth'), ('demand', 'demand')))):
            raise ValueError('Source assessment differs from current native claim/review')
        sources[key] = assessment
    ledger, bindings = [], []
    fields = (*METRICS, 'source_localizable')
    for (event_id, index), (review, claim) in expected.items():
        row = dict.fromkeys(fields)
        row.update(event_id=event_id, claim_index=index, independent_local_event=True,
                   evidence_verified=True, causal_or_passive_scores_used=False)
        if claim['locally_correct'] is True:
            row.update({k: False for k in METRICS[:3]})
            row['source_localizable_failure_candidate'] = False
        elif claim['locally_correct'] is False:
            row['faithful_control_candidate'] = False
        assessment = sources.get((event_id, index))
        if assessment is not None:
            row.update({k: assessment[k] for k in fields if k in assessment})
            row['independent_local_event'] = assessment.get('independent_local_event', True)
            if (row['proper_pilot_failure_event_eligible'] is False and
                    assessment.get('proper_pilot_eligibility_status') == PENDING_LEGACY_STATUS):
                row['proper_pilot_failure_event_eligible'] = None
        if (claim['locally_correct'] is True or claim['demand'] != 'singleton' or
                review['truncation'] is not False):
            if row['proper_pilot_failure_event_eligible'] is True:
                raise ValueError('Source assessment admits a correct, multi-demand or capped failure claim')
            row['proper_pilot_failure_event_eligible'] = False
        ledger.append(row)
        bindings.append(dict(event_id=event_id, claim_index=index,
            semantic_review_object_sha256=object_sha(review), claim_sha256=object_sha(claim),
            source_assessment='EXPLICIT_COORDINATE_OR_COMPILED_SOURCE_REVIEW' if assessment
                              else 'UNASSESSED_SOURCE_READOUT',
            candidate_uniqueness='Canonical manually selected exact claims; repeated prose is not enumerated as extra events.'))
    return ledger, bindings
