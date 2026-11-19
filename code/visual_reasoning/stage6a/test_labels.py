from visual_reasoning.stage6a.labels import aggregate_object_label


def test_uncertain_claim_is_not_a_negative_control():
    assert aggregate_object_label(['visually_supported','unresolved_image'],True)=='UNRESOLVED'


def test_confirmed_hallucination_survives_other_uncertainty():
    assert aggregate_object_label(['hallucination','unresolved_image'],False)=='hallucination'


def test_incomplete_negative_trace_is_unresolved():
    assert aggregate_object_label(['reference_supported'],False)=='UNRESOLVED'


def test_contextual_false_matches_are_not_hallucinations():
    assert aggregate_object_label(['not_object_claim','nonasserted','visually_supported'],True)=='no_detected_object_hallucination'
