"""Check every required GPU artifact before releasing the authorized allocation."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    native_proof = json.loads(Path("outputs/stage8a/audit/native_main_completion_verified_v1.json").read_text())
    assert native_proof["completed"] and native_proof["examples"] == 96
    assert digest(native_proof["completion_receipt"]) == native_proof["completion_receipt_sha256"]
    config_path = Path("outputs/stage8a/config/value_assays_v1.json")
    config = json.loads(config_path.read_text())
    assert digest(config["requests"]) == config["requests_sha256"]
    selected = json.loads(Path(config["requests"]).read_text())
    output = Path(config["output_dir"])
    assert json.loads((output/"wrapper.json").read_text())["completed"]
    paths = {json.loads(p.read_text())["event_id"]:p for p in output.glob("worker*/events/*.json")}
    assert set(paths) == {r["event_id"] for r in selected["requests"]}
    assert len(paths) == len(list(output.glob("worker*/events/*.json")))
    measured, counts = {}, {}
    for split in ("discovery", "confirmation"):
        m = Path(f"outputs/stage8a/measurement/{split}_v1")
        assert json.loads((m/"wrapper.json").read_text())["completed"]
        expected = {r["event_id"] for r in json.loads(Path(f"outputs/stage8a/measurement/{split}_requests_v1.json").read_text())["requests"]}
        observed = set()
        for path in m.glob("worker*/events/*.json"):
            e = json.loads(path.read_text())
            assert e["capture_exact"] and e["self_noop_exact"]
            assert e["event_id"] not in measured and e["split"] == split
            observed.add(e["event_id"])
            measured[e["event_id"]] = e
        assert observed == expected
        counts[split] = len(observed)
    for request in selected["requests"]:
        e = json.loads(paths[request["event_id"]].read_text())
        assert e["completed"] and e["analysis_roles"] == request["analysis_roles"]
        assert len(e["results"]) == 1
        result = e["results"][0]
        assert result["layers"] == [19,20,21,22]
        assert result["self_noop_exact"] and result["selected_routing_fixed"]
        raw = result["token_log_probabilities"]
        assert raw["self"] == raw["native"]
        for arm in ("native", "target_off", "irrelevant_off"):
            assert raw[arm]["original"] == measured[e["event_id"]]["raw_token_log_probabilities"][arm], (e["event_id"], arm)
    record = dict(at=datetime.now(timezone.utc).isoformat(), completed=True, required_gpu_work_complete=True,
                  native_bases=native_proof["examples"], discovery_measurements=counts["discovery"], confirmation_measurements=counts["confirmation"],
                  value_events=len(paths), native_and_off_readouts_match_measurement_exactly=True,
                  value_self_exact=True, selected_routing_fixed=True,
                  config=str(config_path), config_sha256=digest(config_path),
                  value_artifact_sha256={str(p):digest(p) for p in paths.values()},
                  release_authorized=True, slurm_job_id=config["slurm_allocation"])
    target = Path("outputs/stage8a/audit/gpu_work_complete_v1.json")
    assert not target.exists()
    target.write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps({k:v for k,v in record.items() if k != "value_artifact_sha256"}),flush=True)


if __name__ == "__main__":
    main()
