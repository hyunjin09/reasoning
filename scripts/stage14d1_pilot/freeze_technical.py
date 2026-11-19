"""CPU preflight and immutable technical execution seal."""
import ast
import hashlib
from pathlib import Path
from scripts.stage14d1.contracts_v3 import validate_query as legacy_validate
from scripts.stage14d1_pilot.common import *


def main():
    for p in Path("scripts/stage14d1_pilot").glob("*.py"):
        ast.parse(p.read_text(), filename=str(p))
    for sealpath in [OLD / "audit/final_package_seal.json",
                     RECOVERY / "audit/recovery_closure_seal.json"]:
        seal = load(sealpath)
        for group in ("package_files", "code_files"):
            for path, expected in seal[group].items():
                assert sha(path) == expected, path
    legacy = load(RECOVERY / "raw/independent_validation_b8/acquisition_states.json")["cases"]
    families = {r["item_id"]: r for r in rows(P / "inference/families.jsonl")}
    original_regression = []
    for item, state in legacy.items():
        row = families[item]
        ok, reason = legacy_validate(state["query"], row["question"], row["prefix"])
        assert not ok and reason == "UNSUPPORTED_NUMBER"
        original_regression.append(dict(item_id=item, accepted=ok, reason=reason))
    save(P / "audit/legacy_eight_regression.json", dict(
        at=now(), cases=original_regression,
        original_rejections_preserved=True, no_retrospective_reclassification=True))
    model = load(P / "protocol/runtime.json")["model"]["model"]
    for name, expected in model["files_sha256"].items():
        assert sha(Path(model["checkpoint"]) / name) == expected, name
    save(P / "audit/model_integrity.json", dict(at=now(), revision=model["revision"], status="PASS"))
    code = list(Path("scripts/stage14d1_pilot").glob("*.py"))
    deps = [Path(f"scripts/stage14d1/{n}") for n in
            ("common.py", "contracts.py", "contracts_v2.py", "contracts_v3.py", "views.py", "run.sh")]
    sources = [p for p in (P / "protocol").glob("*") if p.is_file()]
    sources += [P / "inference/families.jsonl", P / "audit/interface_spec_freeze.json",
                P / "audit/cohort_identity.json", P / "audit/model_integrity.json"]
    save(P / "audit/execution_seal_v4.json", dict(at=now(), files={str(p): sha(p) for p in code+deps+sources}))
    sample = load(P / "protocol/sampler_and_seeds.json")
    save(P / "manifests/technical_v4.json", dict(
        id="technical_v4", mode="technical", families=sample["technical_families"],
        wall_seconds=1800, seal=str(P / "audit/execution_seal_v4.json"),
        no_scientific_main_in_this_job=True))
    print("Frozen technical v4: same8; original artifacts and model hashes PASS")


if __name__ == "__main__":
    main()
