"""Freeze available full MathVision inputs before any Stage8B outcomes."""
import hashlib
import io
import json
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.ipc as ipc
from PIL import Image


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    out=Path("outputs/stage8b")
    old=json.loads(Path("outputs/stage7a/cohort/dataset_inventory.json").read_text())
    source=Path(next(d for d in old["datasets"] if d["dataset"]=="MathVision")["checked_files"][0]["path"])
    assert source.resolve().is_relative_to(Path("/data/dataset"))
    with pa.memory_map(str(source),"r") as handle:
        table=ipc.open_stream(handle).read_all()
    assert table.num_rows==3040
    model=json.loads(Path("outputs/stage8a/audit/input_inventory.json").read_text())
    freeze_path=Path("outputs/stage8a/analysis/discovery_freeze_v1/freeze.json")
    frozen=json.loads(freeze_path.read_text())
    assert frozen["retrieval"]["spec"]==dict(kind="joint",aggregation="max",window=4,C=.01)
    assert sha(frozen["retrieval"]["models"])==frozen["retrieval"]["models_sha256"]
    rows=table.to_pylist()
    order=list(range(len(rows)));random.Random(1234).shuffle(order)
    derived=Path("/data/dataset/reasoning_steps_stage8b/MathVision")
    # Record discovery before any derived image materialization (no download).
    inventory=dict(at=datetime.now(timezone.utc).isoformat(),dataset="MathVision",split="test",rows=len(rows),
        lookup_order=["Project datasets link absent","Exact allowed /data/dataset Arrow from prior inventory verified"],
        source=str(source),source_sha256=sha(source),source_size=source.stat().st_size,
        no_download=True,model_checkpoint=model["model_checkpoint"],model_revision=model["revision"],
        frozen_detector=str(freeze_path),frozen_detector_sha256=sha(freeze_path),
        derived_image_root=str(derived),hf_cache_write=False)
    ip=out/"audit/input_inventory.json";assert not ip.exists();ip.write_text(json.dumps(inventory,indent=2)+"\n")
    with Path("workspace/dataset_inventory.md").open("a") as stream:
        stream.write(f"\n\n## Stage8B input lookup — {inventory['at']}\n\nProject datasets link absent; exact MathVision full test Arrow verified under allowed `/data/dataset` ({len(rows)} rows with embedded image bytes, SHA256 `{inventory['source_sha256']}`). Existing2B model and frozen Stage8A detector available. No download or HF cache write. Derived images for approved census execution are materialized in `{derived}`; raw source is unchanged. Details: `outputs/stage8b/audit/input_inventory.json`.\n")
    derived.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for rank,index in enumerate(order):
        row=rows[index];raw=row["decoded_image"]["bytes"]
        assert raw and row["id"].isdigit()
        with Image.open(io.BytesIO(raw)) as image:
            rgb=image.convert("RGB")
            content=hashlib.sha256(str(rgb.size).encode()+rgb.tobytes()).hexdigest()
            size=list(rgb.size)
        image_path=derived/f"{row['id']}.jpg"
        if image_path.exists():
            assert sha(image_path)==hashlib.sha256(raw).hexdigest()
        else:
            image_path.write_bytes(raw)
        question=row["question"].replace("<image1>","").strip()
        options=row["options"]
        if options:
            question+="\n\nOptions:\n"+"\n".join(f"{chr(65+i)}. {o}" for i,o in enumerate(options))
            query=question+"\n\nReason step by step and put the final option letter in \\boxed{} ."
        else:
            query=question+"\n\nReason step by step and put the final answer in \\boxed{} ."
        manifest.append(dict(order=rank,row_index=index,item_id=row["id"],family_id="mathvision_image_"+content,
            image=str(image_path),image_sha256=hashlib.sha256(raw).hexdigest(),decoded_image_sha256=content,
            image_size=size,question=question,generation_query=query,options=options,answer=row["answer"],
            level=row["level"],subject=row["subject"],seed=1234,transfer_audit=rank<32))
    assert len({r["item_id"] for r in manifest})==3040
    for name,selected in (("census_manifest_v1.jsonl",manifest),("transfer32_manifest_v1.jsonl",manifest[:32])):
        path=out/"cohort"/name;assert not path.exists()
        path.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in selected))
    frozen=dict(at=inventory["at"],rows=len(manifest),families=len({r["family_id"] for r in manifest}),
        subjects=dict(Counter(r["subject"] for r in manifest)),levels=dict(Counter(r["level"] for r in manifest)),
        selected_transfer_items=[r["item_id"] for r in manifest[:32]],selection_seed=1234,outcomes_used=False,
        family_rule="Exact decoded RGB content including dimensions; near duplicates/template aliases remain subject to later input-only audit",
        manifest_sha256=sha(out/"cohort/census_manifest_v1.jsonl"),transfer_sha256=sha(out/"cohort/transfer32_manifest_v1.jsonl"))
    (out/"cohort/input_freeze_v1.json").write_text(json.dumps(frozen,indent=2)+"\n")
    print(json.dumps(frozen,indent=2))


if __name__=="__main__":main()
