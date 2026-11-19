"""Read-only native progress with explicit running/capped accounting."""
import argparse
import json
from datetime import datetime,timezone
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    now=datetime.now(timezone.utc)
    config=json.loads(Path("outputs/stage8a/config/main_native_v1.json").read_text())
    rows=[json.loads(s) for s in Path(config["manifest"]).read_text().splitlines()]
    results=[]
    workers=[]
    for rank in (0,1):
        out=Path(config["output_dir"])/f"worker{rank}"
        completed=[]
        for p in out.glob("examples/*/result.json"):
            r=json.loads(p.read_text())
            g=json.loads((p.parent/"generation.json").read_text())
            completed.append(dict(base_id=r["base_id"],normal_eos=r["normal_eos"],capped=r["truncated"],
                tokens=r["tokens"],seconds=g["runtime"]["elapsed_seconds"],finished_at=r["finished_at"]))
        results.extend(completed)
        active=None
        log=Path(f"runs/stage8a/main_v1_worker_{rank}.log")
        if log.exists():
            for line in log.read_text().splitlines():
                if not line.startswith("{"):
                    continue
                try: event=json.loads(line)
                except json.JSONDecodeError: continue
                if event.get("event")=="start_example":
                    active=event
                elif event.get("event")=="complete_example" and active and event["base_id"]==active["base_id"]:
                    active=None
        if active:
            active=dict(base_id=active["base_id"],started_at=active["at"],elapsed_seconds=(now-datetime.fromisoformat(active["at"])).total_seconds(),
                        generated_tokens=None,note="In-flight token count is not exposed by the frozen native runner; runtime is right-censored")
        workers.append(dict(rank=rank,planned=len(rows[rank::2]),completed=len(completed),active=active,
                            worker_finished=(out/"completed.json").exists()))
    report=dict(at=now.isoformat(),allocation=config["slurm_allocation"],node=config["node"],gpus=2,planned=len(rows),
                completed=len(results),normal_eos=sum(r["normal_eos"] for r in results),capped=sum(r["capped"] for r in results),
                completed_tokens=sum(r["tokens"] for r in results),workers=workers,
                finished_worker_device_hours=sum(r["seconds"] for r in results)/3600,
                running_device_hours_lower_bound=sum(w["active"]["elapsed_seconds"] for w in workers if w["active"])/3600,
                remaining_examples=len(rows)-len(results),completed_results=results,
                runtime_scope="Sum of per-worker elapsed inference times; not physical GPU accounting, and a brief calibration smoke overlapped these workers.",
                eta_note="The earlier~5h native-only calibration reference is provisional. Do not estimate only from short completed examples while long samples remain censored.")
    # Preserve the original frozen shard accounting; the tail uses the same
    # canonical example directories but distinct execution receipts and logs.
    tail_path=Path("outputs/stage8a/config/main_native_tail_v1.json")
    if tail_path.exists():
        tail=json.loads(tail_path.read_text())
        handoff=json.loads(Path(tail["handoff"]).read_text())
        tail_workers=[]
        for rank in (0,1):
            active=None
            log=Path(f"runs/stage8a/main_native_tail_v1_worker_{rank}.log")
            if log.exists():
                for line in log.read_text().splitlines():
                    if not line.startswith("{"):
                        continue
                    event=json.loads(line)
                    if event.get("event")=="start_example":
                        active=dict(base_id=event["base_id"],started_at=event["at"],
                                    elapsed_seconds=(now-datetime.fromisoformat(event["at"])).total_seconds())
                    elif event.get("event")=="complete_example" and active and active["base_id"]==event["base_id"]:
                        active=None
            tail_workers.append(dict(rank=rank,assigned=handoff["assignments"][str(rank)],active=active,
                finished=(Path(tail["output_dir"])/f"worker{rank}/completed.json").exists()))
        receipt=Path(tail["output_dir"])/"wrapper.json"
        report["tail_handoff"]=dict(workers=tail_workers,completion_receipt=str(receipt),
            reconciliation=json.loads(receipt.read_text()) if receipt.exists() else None,
            note="Original worker0 stops at the reserved-directory guard; final completion is the tail reconciliation, not the original wrapper exit.")
        report["running_device_hours_lower_bound"]+=sum(w["active"]["elapsed_seconds"] for w in tail_workers if w["active"])/3600
    if args.output:
        assert not args.output.exists()
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
