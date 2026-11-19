import json
from pathlib import Path

from transformers import AutoProcessor

from visual_reasoning.stage0.modeling import (
    _incremental_decode_pieces,
    _incremental_decode_pieces_reference,
)


ROOT = Path(__file__).resolve().parents[2]
MODEL = Path(
    "/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/"
    "snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e"
)


def test_linear_bytelevel_decode_matches_reference_on_unicode_boundaries():
    tokenizer = AutoProcessor.from_pretrained(MODEL, local_files_only=True).tokenizer
    token_ids = tokenizer.encode("hello é漢字 😊<|im_end|>", add_special_tokens=False)

    assert _incremental_decode_pieces(tokenizer, token_ids) == _incremental_decode_pieces_reference(
        tokenizer, token_ids
    )


def test_linear_bytelevel_decode_matches_saved_long_generation():
    tokenizer = AutoProcessor.from_pretrained(MODEL, local_files_only=True).tokenizer
    generation_path = (
        ROOT
        / "outputs/stage3b9/prospective_generation/raw/shard_00/examples/3519/generation.json"
    )
    if not generation_path.is_file():
        return
    token_ids = json.loads(generation_path.read_text(encoding="utf-8"))["generated_token_ids"]

    fast = _incremental_decode_pieces(tokenizer, token_ids)
    pieces = [json.loads(line)["decoded_token"] for line in (
        generation_path.parent / "tokens.jsonl"
    ).read_text(encoding="utf-8").splitlines()]

    assert fast[0] == pieces
    assert fast[1] == "".join(pieces)
    assert fast[2] is True
