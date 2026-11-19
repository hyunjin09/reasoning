#!/usr/bin/env python3
"""Apply frozen score-blind construction overrides to fresh edit specifications."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_jsonl
from visual_reasoning.stage3c8.fresh import apply_edit_spec_overrides


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specs", type=Path, required=True)
    parser.add_argument("--overrides", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    args = parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    specs = read_jsonl(args.specs)
    overrides = read_jsonl(args.overrides)
    rows = apply_edit_spec_overrides(specs, overrides)
    write_jsonl(args.output, rows)
    print(json.dumps({
        "source_specs": len(specs),
        "overrides": len(overrides),
        "output_specs": len(rows),
        "score_blind": True,
    }, indent=2))


if __name__ == "__main__":
    main()
