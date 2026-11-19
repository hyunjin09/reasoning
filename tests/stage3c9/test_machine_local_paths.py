from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_dataset_root_is_loaded_from_frozen_config() -> None:
    for relative in (
        "scripts/stage3c9/prepare_config.py",
        "scripts/stage3c9/make_review_packets.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert 'Path("/data/dataset/MathVerse")' not in source
        assert 'dataset_root' in source
