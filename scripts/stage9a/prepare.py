"""Freeze Stage9A's unused families, model identities and blinded native tasks."""
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from scripts.stage8c.prepare import save, sha
from visual_reasoning.stage8c.cohort import proportional_sample, distribution
from visual_reasoning.stage8b.v2_protocol import generation_parameters, MIN_PIXELS, MAX_PIXELS
from visual_reasoning.stage9a.protocol import ARMS, item_seed, prompt, TAU

ROOT = Path("outputs/stage9a/v1")


def main():
    reserve = Path("outputs/stage8c_v2/v1/audit/remaining_family_representatives.json")
    rows = proportional_sample(json.loads(reserve.read_text())["rows"],128,random.Random(920260923))
    models = {}
    for key, name, revision in [
        ("instruct", "Qwen3-VL-2B-Instruct", "89644892e4d85e24eaac8bacfd4f463576704203"),
        ("thinking", "Qwen3-VL-2B-Thinking", "33e0ad94c327808ebc7d3bbc97e78e600f1eeecd")]:
        base = Path("/data/dataset/huggingface/hub")/("models--Qwen--"+name)/"snapshots"/revision
        assert base.is_dir()
        models[key] = dict(checkpoint=str(base), revision=revision,
            files_sha256={p.name:sha(p) for p in sorted(base.iterdir()) if p.is_file()})
    native = []
    for i,row in enumerate(rows):
        assert sha(row["image"]) == row["image_sha256"]
        row.update(order=i, seed=item_seed(row["item_id"]), protocol_id="stage9a_native_v1")
        for arm in ARMS:
            task = {k:row[k] for k in ("item_id","family_id","image","image_sha256","question","seed")}
            task.update(arm=arm, task_id=arm+"_"+row["item_id"], order=i,
                        generation_query=prompt(row["generation_query"], arm))
            native.append(task)
    at = datetime.now(timezone.utc).isoformat()
    save(ROOT/"stage9a_cohort_manifest.json",dict(at=at,rows=rows,independent_families=128,
        reserve=str(reserve),reserve_sha256=sha(reserve),selection_seed=920260923,
        distribution=distribution(rows),prior_results_used=False,
        subtype_note="Subject provides a problem-category proxy; finer image subtype awaits masked annotation.",
        length_note="No output-length selection; reasoning length is measured after generation."))
    save(ROOT/"audit/native_tasks.json",dict(at=at,rows=native,gold_masked=True))
    freeze = Path("outputs/stage8a/analysis/discovery_freeze_v1/freeze.json")
    rule=json.loads(freeze.read_text());assert rule["retrieval"]["tau_R"] == TAU
    sources = ["code/visual_reasoning/stage0/modeling.py", "code/visual_reasoning/stage8a/protocol.py",
        "code/visual_reasoning/stage8b/v2_protocol.py", "code/visual_reasoning/stage8b/passive.py",
        "code/visual_reasoning/stage8b/single_execution.py", "scripts/stage8b/run_native_v2_shared.py",
        "code/visual_reasoning/stage9a/protocol.py", "scripts/stage9a/run_native.py",
        "scripts/stage9a/run_native.sh", "scripts/stage9a/prepare.py",
        "plan/stage9a_execution_protocol_v1.md", "plan/stage9a_thinking_vs_cot_visual_access_regimes_plan.md"]
    save(ROOT/"stage9a_generation_config.json",dict(at=at,models=models,
        generation_parameters=generation_parameters(),presence_penalty=0.,max_new_tokens=40960,
        dtype="bfloat16",min_pixels=MIN_PIXELS,max_pixels=MAX_PIXELS,arms=list(ARMS),
        native_tasks=str(ROOT/"audit/native_tasks.json"),native_tasks_sha256=sha(ROOT/"audit/native_tasks.json"),
        detector_freeze=str(freeze),detector_freeze_sha256=sha(freeze),threshold=TAU,
        allowed_nodes=["node02","node03","node06"],max_total_gpus=4,root=str(ROOT),
        source_sha256={p:sha(p) for p in sources}))
    print(json.dumps(dict(prepared=True,items=128,families=128,tasks=len(native),distribution=distribution(rows))))


if __name__ == "__main__":
    main()
