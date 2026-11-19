"""Seal explicit manual prefix reviews against the fresh2B native artifacts."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage8a.annotations import align_reviewed_event


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--revision", type=int, default=1)
    args = parser.parse_args()
    packet = json.loads(args.packet.read_text())
    assert packet["source_image_reviewed"] and packet["effects_blind"]
    native = Path(packet["native_dir"])
    row = json.loads((native/"manifest_row.json").read_text())
    assert row["base_id"] == packet["base_id"] and row["split"] in {"discovery", "confirmation"}
    assert digest(row["image"]) == row["image_sha256"]
    assert digest(row["asset_metadata"]) == row["asset_metadata_sha256"]
    tokens = [json.loads(line) for line in (native/"tokens.jsonl").read_text().splitlines()]
    coverage = int(packet["reviewed_prefix_tokens"])
    assert 0 < coverage <= len(tokens)
    events = []
    for index, review in enumerate(packet["events"]):
        label = review["label"]
        assert label in {"T", "M", "nearby", "nonvisual"}
        assert review["rationale"] and review["history_evidence"]
        assert review["fresh_visual_demand"] == (label == "T")
        source = review.get("source_id")
        if source is not None:
            assert source in row["facts"] and review["source_identity_valid"]
        if label == "T":
            assert source is not None
        aligned = align_reviewed_event(tokens[:coverage], quote=review["quote"], value=review["readout"], occurrence=review.get("quote_occurrence"))
        assert aligned["evidence_end_token"] < coverage, "Must review the complete upcoming local claim"
        aligned.pop("history_text")
        events.append(dict(**aligned, **{k:v for k,v in review.items() if k not in aligned},
                           event_id=f"main_{row['base_id']}_{label}_{index}", base_id=row["base_id"],
                           family_id=row["family_id"], split=row["split"], source_image_reviewed=True,
                           full_event_prefix_reviewed=True, effects_blind=True))
    assert len({e["prefix_length"] for e in events}) == len(events), "Do not label one query twice"
    result = dict(base_id=row["base_id"], family_id=row["family_id"], split=row["split"],
                  native_dir=str(native), annotated_at=datetime.now(timezone.utc).isoformat(),
                  reviewer="primary research agent", reviewed_prefix_tokens=coverage,
                  total_native_tokens=len(tokens), whole_trajectory_reviewed=coverage==len(tokens),
                  source_image=row["image"], source_image_sha256=digest(row["image"]),
                  asset_metadata=row["asset_metadata"], asset_metadata_sha256=digest(row["asset_metadata"]),
                  native_artifact_sha256={name:digest(native/name) for name in ("input.json", "generation.json", "tokens.jsonl", "manifest_row.json", "result.json")},
                  packet=str(args.packet), packet_sha256=digest(args.packet), events=events,
                  notes=packet.get("notes",[]), unavailable=packet.get("unavailable",[]))
    assert args.revision >= 1
    suffix = "" if args.revision == 1 else f"_v{args.revision}"
    output = Path(f"outputs/stage8a/annotations/main_v1/{row['base_id']}{suffix}.json")
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("x") as f:
        f.write(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(dict(base_id=row["base_id"],events=[(e["event_id"],e["prefix_length"]) for e in events],coverage=coverage)))


if __name__ == "__main__":
    main()
