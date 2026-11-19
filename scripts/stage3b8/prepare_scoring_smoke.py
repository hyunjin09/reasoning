#!/usr/bin/env python3
"""Freeze the first primary base as the Stage 3B.8 implementation smoke test."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import write_jsonl


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    source = ROOT / "outputs/stage3b6/config/primary_manifest.jsonl"
    target = ROOT / "outputs/stage3b8/config/scoring_smoke_manifest.jsonl"
    if target.exists():
        raise FileExistsError("Stage 3B.8 scoring smoke manifest is already frozen")
    first = json.loads(next(line for line in source.read_text(encoding="utf-8").splitlines() if line.strip()))
    if str(first["base_problem_id"]) != "119":
        raise RuntimeError("Expected frozen primary base 119 as the implementation smoke")
    write_jsonl(target, [first])
    print("froze Stage 3B.8 scoring smoke base 119")


if __name__ == "__main__":
    main()
