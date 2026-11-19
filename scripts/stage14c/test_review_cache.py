import pytest
from scripts.stage14c import review_packets_v2 as review


def test_review_membership_is_fixed_and_bound_to_raw_seal(tmp_path,monkeypatch):
    monkeypatch.setattr(review,'ROOT',tmp_path)
    (tmp_path/'audit').mkdir()
    raw=tmp_path/'audit/main_raw_seal.json';raw.write_text('{"fixed":true}')
    calls=[]
    def selector(model):
        calls.append(model);return ['frozen-hash-item','ambiguous-item']
    monkeypatch.setattr(review.scoring,'audit_selection',selector)
    assert review.frozen_audit('I')==['frozen-hash-item','ambiguous-item']
    assert review.frozen_audit('I')==['frozen-hash-item','ambiguous-item']
    assert calls==['I']
    raw.write_text('{"fixed":false}')
    with pytest.raises(AssertionError):review.frozen_audit('I')
