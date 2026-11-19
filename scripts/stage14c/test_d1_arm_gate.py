import pytest
from scripts.stage14c import d1_review_arm as review

def test_completed_arm_only_before_global_seal(tmp_path,monkeypatch):
    monkeypatch.setattr(review,'ROOT',tmp_path);(tmp_path/'audit').mkdir()
    for model in 'IT':
        with pytest.raises(AssertionError):review.guard(model)
    (tmp_path/'audit/D1_I_raw_seal.json').write_text('{}')
    review.guard('I')
    with pytest.raises(AssertionError):review.guard('T')
    (tmp_path/'audit/D1_raw_seal.json').write_text('{}')
    review.guard('T')
