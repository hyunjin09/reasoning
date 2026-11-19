"""Conservative aggregation of reviewed object-presence claims."""


def aggregate_object_label(statuses, complete):
    statuses=set(statuses)
    allowed={'hallucination','unresolved_image','pending_image_review',
             'reference_supported','visually_supported','not_object_claim','nonasserted'}
    if statuses-allowed:raise ValueError(statuses-allowed)
    if 'hallucination' in statuses:return 'hallucination'
    if not complete or statuses&{'unresolved_image','pending_image_review'}:return 'UNRESOLVED'
    return 'no_detected_object_hallucination'
