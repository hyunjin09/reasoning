"""CPU-only gate evidence and throughput; never self-authorizes semantic review."""
import argparse
from pathlib import Path
from scripts.stage14d1_pilot.common import *
from scripts.stage14d1.contracts_v3 import parse_record
from scripts.stage14d1.contracts import valid_readout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("attempt")
    args = parser.parse_args()
    root = P / "raw" / args.attempt
    assert load(root / "exit.json")["status"] == "COMPLETE"
    states = [load(p) for p in sorted((root / "states").glob("*.json"))]
    controls = load(root / "controls.json")["cases"]
    expected_controls = 2 * len(load(P / "protocol/technical_controls_v5.json")["cases"])
    control_valid = len(controls) == expected_controls and all(c["valid"] and not c["cap_hit"] for c in controls)
    branch_reachable = all(any(c["repeat"] == rep and c["expected"] == branch and c["valid"] and c["parsed"]["status"] == branch for c in controls) for rep in ("a", "b") for branch in ("QUERY", "NONE"))
    replay = load(root / "replay.json")["cases"]
    records = {row["item_id"]: row for row in rows(P / "inference/families.jsonl")}
    identities, read_checks = [], []
    receipts = set(root.glob("*/result.json"))
    for state in states:
        refs=[state["query_generation"],state["locator_generation"]]
        refs += [meta["generation_path"] for meta in state["readouts"].values()]
        receipts.update(Path(ref).parent/"result.json" for ref in refs if ref)
    for p in sorted(receipts):
        receipt = load(p)
        assert sha(p.parent / "generation.json") == receipt["generation_sha256"]
        assert sha(p.parent / "input.json") == receipt["input_sha256"]
        inp = load(p.parent / "input.json")
        generation = load(p.parent / "generation.json")
        if inp["kind"] == "solver":
            row = records[inp["item_id"]]
            base = row["original_chat_prompt"] + row["prefix"]
            old = load(RECOVERY / "raw/independent_validation_b8" /
                       f"sampled_0_{inp['item_id']}_a/generation.json")
            expected = old["prompt"]
            identities.append(dict(
                request_id=inp["id"], prefix_bytes=inp["prompt"].startswith(base),
                prefix_tokens=generation["prompt_token_ids"][:len(expected)] == expected,
                pixels=inp["pixels"] == row["original_image_pixels"],
                image_sizes=inp["sizes"] == row["original_image_sizes"]))
        if inp["kind"] == "read":
            read_checks.append(dict(
                id=inp["id"], valid=valid_readout(parse_record(generation["raw_decoded_response"])),
                cap_hit=generation["cap_hit"]))
    locators = [s for s in states if s["locator_generation"]]
    gates = dict(
        exact_replay=len(replay) == 8 and all(x["exact"] and x["input_token_identity"] for x in replay),
        source_prefix_identity=bool(identities) and all(all(v for k, v in r.items() if k != "request_id") for r in identities),
        independent_controls=control_valid and branch_reachable,
        queries_at_least6=len(states) == 8 and sum(s["query_valid"] for s in states) >= 6,
        actionable_at_least4=sum(s["query_valid"] and s["query"]["status"] == "QUERY" for s in states) >= 4,
        read_contract_at_least80pct=bool(read_checks) and sum(r["valid"] for r in read_checks)/len(read_checks) >= .8,
        locator_contract_at_least75pct=bool(locators) and sum(s["address_valid"] for s in locators)/len(locators) >= .75,
        all_logical_slots_mapped=len(states) == 8 and all(len(s["continuation_paths"]) == 6 for s in states))
    readiness_names=("exact_replay","source_prefix_identity","independent_controls","all_logical_slots_mapped")
    execution_ready=all(gates[name] for name in readiness_names)
    timing = [load(p) for p in (root / "timings").glob("*.json")]
    continuation = [t for t in timing if t["task_ids"] and
                    all(load(root / rid / "input.json")["kind"] == "solver" and
                        load(root / rid / "input.json")["cap"] == 256 for rid in t["task_ids"])]
    tokens = sum(t["output_tokens"] for t in continuation)
    seconds = sum(t["elapsed_seconds"] for t in continuation)
    result = dict(
        at=now(), attempt=args.attempt, gates=gates, software_pass=all(gates.values()),
        technical_execution_ready=execution_ready, original_component_gates_pass=all(gates.values()),
        readiness_policy=str(P / "protocol/locator_cardinality_v6.md"),
        source_transport_review_complete=False, source_semantics_not_certified_by_software=True,
        physical_read_checks=read_checks, source_identity_checks=identities,
        query_counts=dict(accepted=sum(s["query_valid"] for s in states),
                          QUERY=sum(s["query_valid"] and s["query"]["status"] == "QUERY" for s in states),
                          NONE=sum(s["query_valid"] and s["query"]["status"] == "NONE" for s in states)),
        locators_attempted=len(locators), locators_valid=sum(s["address_valid"] for s in locators),
        controls_expected_branch_passed=sum(c["passed"] for c in controls),
        controls_total=len(controls), controls_json_provenance_valid=control_valid, controls_branch_reachable=branch_reachable,
        control_semantic_failures=[c for c in controls if not c["passed"]],
        solver_256_tokens=tokens, solver_256_batch_seconds=seconds,
        solver_short_tokens_per_gpu_second=tokens/seconds if seconds else None,
        timings=timing, environment=load(root / "environment.json"),
        source_packets=str(P / "data/source_packets" / args.attempt))
    save(P / "audit" / f"{args.attempt}_gates.json", result)
    print("ORIGINAL_COMPONENT_GATES", result["software_pass"], "EXECUTION_READY", execution_ready, gates,
          "short_solver_tokens_per_second", result["solver_short_tokens_per_gpu_second"])


if __name__ == "__main__":
    main()
