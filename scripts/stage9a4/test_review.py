import pytest
from scripts.stage9a4 import review
from scripts.stage9a4.common import save,sha


def test_manual_review_cannot_seal_against_wrong_packet(tmp_path,monkeypatch):
    monkeypatch.setattr(review,'ROOT',tmp_path)
    save(tmp_path/'audit/full_review_packet.json',dict(literal_adapter_sha256=sha('scripts/stage9a3/literal_review.py'),
        rows=[dict(query_id='a',policy='full',requires_manual=True)]))
    save(tmp_path/'audit/full_manual_review.json',dict(sealed=True,gold_opened=False,packet_sha256='wrong',rows=[]))
    with pytest.raises(AssertionError):review.seal('full')
