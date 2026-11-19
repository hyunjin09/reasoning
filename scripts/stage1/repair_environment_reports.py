#!/usr/bin/env python3
"""Repair Stage 1 environment generation lines from authoritative configs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json, write_text
from visual_reasoning.stage1.reporting import generation_environment_line


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    changes = []
    inspected = 0
    for environment_path in sorted(args.root.resolve().rglob("environment.md")):
        config_path = environment_path.parent / "config.json"
        if not config_path.is_file():
            continue
        config = read_json(config_path)
        signature = config.get("run_signature", {})
        parameters = signature.get("parameters")
        protocol = signature.get("protocol", signature.get("condition"))
        if not isinstance(parameters, dict) or protocol not in {"official", "greedy"}:
            continue
        inspected += 1
        lines = environment_path.read_text(encoding="utf-8").splitlines()
        indices = [index for index, line in enumerate(lines) if line.startswith("- Generation:")]
        if len(indices) != 1:
            raise RuntimeError(f"Expected one generation line in {environment_path}, found {len(indices)}")
        index = indices[0]
        correct = generation_environment_line(str(protocol), parameters)
        if lines[index] == correct:
            continue
        previous = lines[index]
        lines[index] = correct
        write_text(environment_path, "\n".join(lines))
        changes.append(
            {
                "path": str(environment_path),
                "config": str(config_path),
                "previous_line": previous,
                "repaired_line": correct,
                "protocol": protocol,
                "parameters": parameters,
            }
        )
    report = {
        "reason": "Stage 1 inherited a Stage 0 environment prose line hard-coded to greedy decoding; sibling config.json files were authoritative and inference was unchanged.",
        "inspected_reports": inspected,
        "changed_reports": len(changes),
        "inference_rerun": False,
        "configs_changed": False,
        "generations_changed": False,
        "tokens_changed": False,
        "attention_changed": False,
        "statuses_changed": False,
        "changes": changes,
    }
    write_json(args.output, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
