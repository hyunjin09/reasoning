"""Reconcile the unchanged cohort after the explicitly recorded tail handoff."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from harness_state import mutate_gpu_queue
from visual_reasoning.stage8a.native_handoff import boundary_complete


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    config_path = Path("outputs/stage8a/config/main_native_tail_v1.json")
    config = json.loads(config_path.read_text())
    out = Path(config["output_dir"])
    code = int(sys.argv[1])
    evidence = dict(completed=False, exit_code=code, finished_at=datetime.now(timezone.utc).isoformat(),
                    slurm_job_id=config["slurm_allocation"], config_sha256=digest(config_path))
    try:
        assert code == 0
        handoff = json.loads(Path(config["handoff"]).read_text())
        assert boundary_complete(handoff)
        workers = [json.loads((out/f"worker{rank}/completed.json").read_text()) for rank in (0, 1)]
        assert all(w["completed"] for w in workers)
        assert {r["base_id"] for w in workers for r in w["results"]} == set(handoff["pending"])
        assert digest(config["preserved_artifact_ledger"]) == config["preserved_artifact_ledger_sha256"]
        ledger = json.loads(Path(config["preserved_artifact_ledger"]).read_text())
        for path, expected in ledger["sha256"].items():
            assert digest(path) == expected, path
        assert digest(config["manifest"]) == config["manifest_sha256"]
        rows = [json.loads(s) for s in Path(config["manifest"]).read_text().splitlines()]
        root = Path(handoff["canonical_output_dir"])
        results, hashes = [], {}
        for i, row in enumerate(rows):
            path = root/f"worker{i%2}/examples"/row["base_id"]
            assert json.loads((path/"manifest_row.json").read_text()) == row
            result = json.loads((path/"result.json").read_text())
            generation = json.loads((path/"generation.json").read_text())
            assert result["base_id"] == row["base_id"] and result["family_id"] == row["family_id"]
            assert len((path/"tokens.jsonl").read_text().splitlines()) == result["tokens"]
            assert generation["seed"] == config["seed"] and generation["model_revision"] == config["model_revision"]
            assert result["normal_eos"] or result["at_length_cap"]
            results.append(result)
            hashes[str(path/"result.json")] = digest(path/"result.json")
        assert len(results) == len({r["base_id"] for r in results}) == 96
        evidence.update(completed=True, examples=96, normal_eos=sum(r["normal_eos"] for r in results),
                        capped=sum(r["truncated"] for r in results), result_sha256=hashes,
                        previously_completed_artifacts_unchanged=True,
                        original_wrapper_preserved=str(root/"wrapper.json"),
                        note="Original exit at reserved345 is intentional after current19 completed. This receipt reconciles96unique native results; no completed sample was regenerated.")
    except Exception as error:
        evidence["error"] = repr(error)
    target = out/"wrapper.json"
    with target.open("x") as f:
        f.write(json.dumps(evidence, indent=2)+"\n")
    def update(queue):
        job = next(j for j in queue["jobs"] if j["id"] == "stage8a_main_native_tail_v1")
        job.update(status="succeeded" if evidence["completed"] else "failed", **evidence)
        original = next(j for j in queue["jobs"] if j["id"] == "stage8a_main_native_v1")
        original["notes"] = "User-approved tail handoff; original no-overwrite assertion is the expected boundary. See " + str(target)
        original["completion_reconciliation"] = str(target)
    mutate_gpu_queue(Path.cwd(), update)
    print(json.dumps(evidence), flush=True)
    if not evidence["completed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
