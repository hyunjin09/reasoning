from scripts.stage6a.summarize_release import c1_availability_summary


def test_capped_stress_does_not_erase_validated_assets():
    conditions = {'base': {'intact', 'mild', 'strong', 'mask', 'counterfactual'}}
    counts = c1_availability_summary(['base'], conditions, lambda key, condition: condition == 'intact')
    assert counts['mean_available_conditions'] == 4
    assert counts['counterfactual_and_mask_available_pairs'] == 1
    assert counts['mean_eos_conditions'] == 1
    assert counts['counterfactual_and_mask_eos_pairs'] == 0


def test_missing_mask_cannot_count_as_available_pair():
    conditions = {'base': {'intact', 'mild', 'counterfactual'}}
    counts = c1_availability_summary(['base'], conditions, lambda key, condition: condition in conditions[key])
    assert counts['mean_available_conditions'] == 2
    assert counts['counterfactual_and_mask_available_pairs'] == 0
    assert counts['mean_eos_conditions'] == 2
    assert counts['counterfactual_and_mask_eos_pairs'] == 0
