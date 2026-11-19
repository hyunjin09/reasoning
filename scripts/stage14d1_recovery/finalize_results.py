"""CPU-only result verification; no relabeling, inference or follow-on launch."""
import json
import re
import subprocess

from jsonschema import Draft7Validator

from scripts.stage14d1.contracts_v3 import SCHEMAS, validate_query
from scripts.stage14d1_recovery.contracts import OLD, R, load, now, rows, save, sha


def provenance_audit(query, row):
    fields = ["subgoal", "entity", "entity_id", "predicate", "spatial_reference", "query"]
    needed = set(re.findall(r"\d+(?:\.\d+)?", " ".join(query[k] for k in fields)))
    entries = []
    supported = set()
    for p in query["numeric_provenance"]:
        exact = p["quote"] in row[p["source"]]
        digit = p["number"] in re.findall(r"\d+(?:\.\d+)?", p["quote"])
        if exact and digit:
            supported.add(p["number"])
        entries.append(dict(
            **p, exact_quote_in_claimed_source=exact, literal_number_in_quote=digit,
            number_used_in_query_fields=p["number"] in needed))
    return dict(
        numbers_requiring_citation=sorted(needed), entries=entries,
        numbers_without_valid_literal_citation=sorted(needed - supported))


def main():
    target = R / "audit/final_result_verification.json"
    assert not target.exists(), "Preserve existing verification"
    result = load(R / "audit/technical_revalidation_results.json")
    family_map = {row["item_id"]: row for row in rows(R / "data/families.jsonl")}
    schema = Draft7Validator(SCHEMAS["query"])
    controls = []
    for c in result["controls"]:
        controls.append(dict(
            id=c["id"], repeat=c["repeat"], expected=c["expected"],
            actual_branch=c["parsed"]["status"],
            branch_only_match=c["parsed"]["status"] == c["expected"],
            json_schema_valid=schema.is_valid(c["parsed"]),
            full_contract_valid=c["contract_valid"], reason=c["reason"],
            cap_hit=c["cap_hit"]))
    cases = []
    for item, state in result["acquisition_cases"].items():
        query = state["query"]
        row = family_map[item]
        valid, reason = validate_query(query, row["question"], row["prefix"])
        assert (valid, reason) == (state["query_valid"], state["query_reason"])
        base = R / "raw/independent_validation_b8" / f"{item}_query"
        generation = load(base / "generation.json")
        cases.append(dict(
            item_id=item, family_id=row["family_id"],
            raw_path=str(base / "generation.json"),
            raw_sha256=sha(base / "generation.json"),
            input_path=str(base / "input.json"),
            json_schema_valid=schema.is_valid(query), branch=query["status"],
            full_contract_valid=valid, reason=reason,
            finish_reason=generation["finish_reason"], cap_hit=generation["cap_hit"],
            provenance=provenance_audit(query, row)))

    schedules = {}
    for profile in ["default_b8", "deterministic_b8"]:
        raw = rows(R / "traces" / profile / "schedule.jsonl")
        schedules[profile] = {}
        for rep in ["a", "b"]:
            request = f"rng_33_{rep}"
            selected = [s for s in raw if request in s["tokens"]]
            schedules[profile][rep] = selected[:3]

    receipts = list((R / "raw").glob("*/*/result.json"))
    kinds = {}
    for p in receipts:
        receipt = load(p)
        assert sha(p.parent / "input.json") == receipt["input_sha256"]
        assert sha(p.parent / "generation.json") == receipt["generation_sha256"]
        kind = load(p.parent / "input.json")["kind"]
        kinds[kind] = kinds.get(kind, 0) + 1
    old = load(OLD / "audit/final_package_seal.json")
    for group in ["package_files", "code_files"]:
        for p, expected in old[group].items():
            assert sha(p) == expected, p
    execution = load(R / "audit/execution_seal.json")
    for p, expected in execution["files"].items():
        assert sha(p) == expected, p
    account = load(R / "audit/resource_accounting.json")
    assert account["total_GPU_hours"] < 2
    slurm = subprocess.check_output([
        "sacct", "-j", "146598,146599", "-X", "-n", "-P",
        "--format=JobID,State,ExitCode,ElapsedRaw,AllocTRES,NodeList"], text=True)
    terminal = [line.split("|") for line in slurm.splitlines() if line]
    assert len(terminal) == 2 and all(row[1] == "COMPLETED" for row in terminal)
    assert len(cases) == 8 and len(controls) == 12 and len(receipts) == 268
    assert all(c["json_schema_valid"] and not c["cap_hit"] for c in cases + controls)
    assert all(c["branch_only_match"] for c in controls)
    assert sum(c["full_contract_valid"] for c in controls) == 10
    assert sum(c["full_contract_valid"] for c in cases) == 0
    assert result["attempted_locators"] == 0
    assert len(result["read_records"]) == 8 and all(r["valid"] for r in result["read_records"])
    save(target, dict(
        at=now(), decision="NO_GO_TECHNICAL_QUERY_CONTRACT",
        exact_replay_gate=result["gates"]["independent_exact_replay"],
        controls=controls, scientific_case_queries=cases,
        case33_prefill_schedules=schedules, completed_receipts=len(receipts),
        request_kinds=kinds, locator_status="NOT_ATTEMPTED_NO_ELIGIBLE_QUERY",
        preservation=dict(original_package_files=len(old["package_files"]),
                          original_code_files=len(old["code_files"]),
                          recovery_execution_files=len(execution["files"]),
                          all_hashes_match=True),
        raw_sacct=slurm, resource_accounting=account,
        no_new_model_calls=True, no_scientific_pilot=True,
        interpretation="Strict provenance rejection is distinct from JSON syntax "
                       "failure and from demonstrated false visual evidence."))
    print("Verified: replay PASS; branch/syntax 12/12; controls contract10/12; "
          "scientific queries syntax8/8, contract0/8; pilot NO-GO.")


if __name__ == "__main__":
    main()
