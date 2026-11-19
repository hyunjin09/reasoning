"""Create masked demand packets; publish native tables only after all384 finish.

Safe to call after each worker. No detector features, accuracy or causal scores
are opened. Atomic packet claims keep concurrent exporters from duplicating work.
"""
import argparse
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path

from scripts.stage8c.prepare import save,sha
from visual_reasoning.stage9a.demands import nominate
from visual_reasoning.stage9a.protocol import ARMS


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",type=Path,default=Path("outputs/stage9a/v1"));args=ap.parse_args()
    root=args.root
    tasks=json.loads((root/"audit/native_tasks.json").read_text())["rows"]
    records=[]
    for task in tasks:
        directory=root/"native/examples"/task["task_id"]
        receipt=directory/"result.json"
        if not receipt.exists():
            continue
        result=json.loads(receipt.read_text())
        packet_id="p_"+hashlib.sha256(("stage9a_packet:"+task["task_id"]).encode()).hexdigest()[:20]
        target=root/"annotations/packets"/packet_id
        try:
            target.mkdir(parents=True,exist_ok=False)
        except FileExistsError:
            if not (target/"packet.json").exists():
                continue  # Another exporter may currently own this packet.
        else:
            for name in ("tokens.jsonl","generation.json"):
                assert sha(directory/name)==result["provenance_sha256"][str(directory/name)]
            token_rows=[json.loads(x) for x in (directory/"tokens.jsonl").read_text().splitlines()]
            span=result["reasoning_span"]
            events=nominate(token_rows,span["start"],span["end"],task["task_id"])
            save(target/"packet.json",dict(packet_id=packet_id,question=task["question"],image=task["image"],
                image_sha256=task["image_sha256"],events=events,
                review_requirements=["accept/reject/unknown semantic visual demand and kind",
                    "verbatim evidence and exact demanded source identity/ROI",
                    "native/counterfactual local evidence strings, if eligible",
                    "irrelevant and semantic donor ROI, if eligible"],
                masking="No arm ID, model checkpoint, gold/correctness, routing or causal results; text style may reveal arm.",
                coverage="At most earliest explicit visual mention per quarter; empty quarters do not certify absence."))
        records.append(dict(packet_id=packet_id,task_id=task["task_id"],receipt=str(receipt),receipt_sha256=sha(receipt)))
    complete=all((root/"native/examples"/t["task_id"]/"result.json").exists() for t in tasks)
    if complete and len(records)==384:
        lock=root/"audit/native_export_claim"
        try:
            lock.mkdir()
        except FileExistsError:
            return
        import pandas as pd
        collected={arm:[] for arm in ARMS}
        for task in tasks:
            d=root/"native/examples"/task["task_id"]
            r=json.loads((d/"result.json").read_text());g=json.loads((d/"generation.json").read_text())
            span=r["reasoning_span"]
            collected[task["arm"]].append(dict(task_id=task["task_id"],item_id=task["item_id"],
                family_id=task["family_id"],arm=task["arm"],seed=task["seed"],
                generated_tokens=r["tokens"],reasoning_start=span["start"],reasoning_end=span["end"],
                reasoning_tokens=span["end"]-span["start"],common_assistant_end=span["common_end"],
                boundary=span["boundary"],boundary_certain=span["certain"],completion=r["completion"],
                normal_eos=r["normal_eos"],at_length_cap=r["at_length_cap"],
                response=g["raw_decoded_response"],generated_token_ids=g["generated_token_ids"],
                runtime_seconds=r["runtime"]["elapsed_seconds"],artifact_dir=str(d),receipt_sha256=sha(d/"result.json")))
        table_paths=[]
        for arm,rows in collected.items():
            p=root/f"stage9a_{arm}_trajectories.parquet";assert not p.exists()
            pd.DataFrame(rows).to_parquet(p,index=False);table_paths.append(p)
        save(root/"annotations/packet_index.json",dict(rows=records,complete=True))
        save(root/"audit/native_complete.json",dict(at=datetime.now(timezone.utc).isoformat(),
            complete=True,trajectories=384,items=128,arms=list(ARMS),
            tables_sha256={str(p):sha(p) for p in table_paths},
            next="Complete masked semantic reviews and freeze eligible causal subset before measurements/causal scores.",
            scientific_stage_complete=False))
    print(json.dumps(dict(native_complete=complete,packets_found=len(records),scientific_stage_complete=False)))


if __name__=="__main__":
    main()
