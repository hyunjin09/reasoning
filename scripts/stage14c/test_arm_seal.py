import pytest
from scripts.stage14c import scoring_v5 as scoring


def test_instruct_can_start_after_own_freeze_but_thinking_requires_global(tmp_path,monkeypatch):
    monkeypatch.setattr(scoring,'ROOT',tmp_path);(tmp_path/'audit').mkdir()
    with pytest.raises(AssertionError):scoring.guard('I')
    (tmp_path/'audit/main_I_raw_seal.json').write_text('{}')
    scoring.guard('I')
    with pytest.raises(AssertionError):scoring.guard('T')
    (tmp_path/'audit/main_raw_seal.json').write_text('{}')
    with pytest.raises(AssertionError):scoring.guard('T')
    (tmp_path/'audit/main_I_scoring_seal.json').write_text('{}')
    scoring.guard('T')
