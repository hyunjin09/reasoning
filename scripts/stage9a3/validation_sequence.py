"""Fixed teacher-forcing probes do not require a long native answer."""


def fixed_cache_sequence(native, fallback, count=8):
    assert native and fallback
    return (list(native) + (list(fallback) * count))[:count]


def needs_resume(tokens, eos_ids):
    return tokens[-1] not in eos_ids
