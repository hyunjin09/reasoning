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
    replay = load(root / "replay.json")["cases"]
    records = {row["item_id"]: row for row in rows(P / "inference/families.jsonl")}
    identities, read_checks = [], []
    for p in root.glob("*/result.json"):
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
        independent_controls=len(controls) == 16 and all(c["passed"] for c in controls),
        queries_at_least6=len(states) == 8 and sum(s["query_valid"] for s in states) >= 6,
        actionable_at_least4=sum(s["query_valid"] and s["query"]["status"] == "QUERY" for s in states) >= 4,
        read_contract_at_least80pct=bool(read_checks) and sum(r["valid"] for r in read_checks)/len(read_checks) >= .8,
        locator_contract_at_least75pct=bool(locators) and sum(s["address_valid"] for s in locators)/len(locators) >= .75,
        all_logical_slots_mapped=len(states) == 8 and all(len(s["continuation_paths"]) == 6 for s in states))
    timing = [load(p) for p in (root / "timings").glob("*.json")]
    continuation = [t for t in timing if t["task_ids"] and
                    all(load(root / rid / "input.json")["kind"] == "solver" and
                        load(root / rid / "input.json")["cap"] == 256 for rid in t["task_ids"])]
    tokens = sum(t["output_tokens"] for t in continuation)
    seconds = sum(t["elapsed_seconds"] for t in continuation)
    result = dict(
        at=now(), attempt=args.attempt, gates=gates, software_pass=all(gates.values()),
        source_transport_review_complete=False, source_semantics_not_certified_by_software=True,
        physical_read_checks=read_checks, source_identity_checks=identities,
        query_counts=dict(accepted=sum(s["query_valid"] for s in states),
                          QUERY=sum(s["query_valid"] and s["query"]["status"] == "QUERY" for s in states),
                          NONE=sum(s["query_valid"] and s["query"]["status"] == "NONE" for s in states)),
        locators_attempted=len(locators), locators_valid=sum(s["address_valid"] for s in locators),
        controls_passed=sum(c["passed"] for c in controls),
        solver_256_tokens=tokens, solver_256_batch_seconds=seconds,
        solver_short_tokens_per_gpu_second=tokens/seconds if seconds else None,
        timings=timing, environment=load(root / "environment.json"),
        source_packets=str(P / "data/source_packets" / args.attempt))
    save(P / "audit" / f"{args.attempt}_gates.json", result)
    print("SOFTWARE_PASS", result["software_pass"], gates,
          "short_solver_tokens_per_second", result["solver_short_tokens_per_gpu_second"])


if __name__ == "__main__":
    main()
