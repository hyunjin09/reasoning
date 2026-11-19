from scripts.stage9a3.validation_sequence import fixed_cache_sequence, needs_resume


def test_short_eos_trajectory_does_not_skip_activation_checks():
    assert fixed_cache_sequence([1, 2], [7, 8, 9], 8) == [1, 2, 7, 8, 9, 7, 8, 9]


def test_long_native_sequence_is_unchanged():
    assert fixed_cache_sequence(list(range(20)), [99], 8) == list(range(8))


def test_never_resume_after_eos():
    assert not needs_resume([1, 2], [2, 3])
    assert needs_resume([1, 4], [2, 3])
