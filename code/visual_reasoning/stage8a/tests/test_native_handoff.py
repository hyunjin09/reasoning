import hashlib
import json
import pytest

from visual_reasoning.stage8a.native_handoff import claim_destination


def test_handoff_only_adopts_its_empty_reservation_and_rejects_native_overwrite(tmp_path):
    dest = tmp_path / "345"
    dest.mkdir()
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(dict(reservation=str(dest))))
    (dest / "handoff_reserved.json").write_text(json.dumps(dict(
        handoff_sha256=hashlib.sha256(handoff.read_bytes()).hexdigest())))
    claim_destination(dest, handoff)
    (dest / "input.json").write_text("{}")
    with pytest.raises(FileExistsError, match="native artifacts"):
        claim_destination(dest, handoff)
    other = tmp_path / "425"
    other.mkdir()
    with pytest.raises(FileExistsError):
        claim_destination(other, handoff)
    fresh = tmp_path / "375"
    claim_destination(fresh, handoff)
    assert fresh.is_dir()
