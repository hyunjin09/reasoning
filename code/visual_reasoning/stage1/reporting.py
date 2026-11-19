"""Stage 1 reporting helpers that reflect the locked decoding protocol."""

from __future__ import annotations

from typing import Any

from visual_reasoning.stage0.reporting import environment_markdown


def generation_environment_line(protocol: str, parameters: dict[str, Any]) -> str:
    cap = int(parameters["max_new_tokens"])
    if bool(parameters["do_sample"]):
        return (
            f"- Generation: protocol=`{protocol}`, sampling enabled, temperature=`{parameters['temperature']}`, "
            f"top-p=`{parameters['top_p']}`, top-k=`{parameters['top_k']}`, seed=`{parameters['seed']}`, "
            f"normal stop=`EOS`, safety ceiling=`{cap}` tokens"
        )
    return f"- Generation: protocol=`{protocol}`, sampling disabled, normal stop=`EOS`, safety ceiling=`{cap}` tokens"


def stage1_environment_markdown(info: dict[str, Any], protocol: str, parameters: dict[str, Any]) -> str:
    report = environment_markdown(info)
    lines = report.splitlines()
    replacement = generation_environment_line(protocol, parameters)
    replaced = False
    for index, line in enumerate(lines):
        if line.startswith("- Generation:"):
            lines[index] = replacement
            replaced = True
            break
    if not replaced:
        raise RuntimeError("Stage 0 environment report lacks the expected generation line")
    return "\n".join(lines)
