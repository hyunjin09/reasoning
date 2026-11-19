"""Frozen anchor indexing and Gate-A execution rule."""
def anchor_cutoff(emitted_tokens):
    assert isinstance(emitted_tokens,int) and emitted_tokens>0
    return emitted_tokens-1


def gate_a(visual_drop,text_gain):
    return bool(visual_drop>=.10-1e-12 or text_gain>=.10-1e-12)
