"""Frozen no-oracle SAVA worker; all GPU operations require Slurm."""
import argparse
import hashlib
import importlib.metadata
import os
import socket
import sys
import time
import traceback
from copy import deepcopy
from pathlib import Path

from scripts.stage14d1.contracts import safe_payload, validate_address, valid_readout
from scripts.stage14d1_pilot.interface_v6 import helper_prompt, normalize_address
from scripts.stage14d1.contracts_v3 import compact_prompt, parse_record
from scripts.stage14d1.views import render_views
from scripts.stage14d1_pilot.common import *
from scripts.stage14d1_pilot.execution import continuation_plan, read_plan
from scripts.stage14d1_pilot.interface_v6 import build_catalog, compile_query, query_prompt, validate_query


def run(manifest_path):
    assert os.environ.get("SLURM_JOB_ID")
    assert os.environ.get("VLLM_ENABLE_V1_MULTIPROCESSING") == "0"
    m = load(manifest_path)
    assert m["mode"] in ("technical", "main")
    for path, digest in load(m["seal"])["files"].items():
        assert sha(path) == digest, path
    cfg = load(P / "protocol/runtime_v6.json")
    allrows = {r["family_id"]: safe_payload(r) for r in rows(P / "inference/families.jsonl")}
    work = [allrows[f] for f in m["families"]]
    root = P / "raw" / m["id"]
    assert not root.exists(), "Use a new immutable attempt manifest for recovery"
    for row in work:
        assert sha(row["image"]) == row["image_sha256"]
        assert hashlib.sha256(row["prefix"].encode()).hexdigest() == row["prefix_sha256"]
    if m["mode"] == "main":
        release = load(m["scientific_release"])
        assert release["technical_pass"] and release["source_transport_review_complete"]
        assert release["protocol_sha256"] == sha(P / "protocol/runtime_v6.json")
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    from vllm import LLM, SamplingParams
    from vllm.sampling_params import StructuredOutputsParams
    sys.path.insert(0, str(Path("outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision").resolve()))
    from run_mathv import build_mathv_prompt, prepare_inputs_for_vllm
    versions = {name: importlib.metadata.version(name) for name in cfg["environment"]}
    assert versions == cfg["environment"]
    assert torch.cuda.device_count() == 1
    node = socket.gethostname().split(".")[0]
    assert node in {"node02", "node03", "node06", "node07"}
    start = time.monotonic()
    deadline = start + m["wall_seconds"] - 60
    job = os.environ["SLURM_JOB_ID"]
    processor = AutoProcessor.from_pretrained(cfg["model"]["model"]["checkpoint"])
    llm = LLM(
        model=cfg["model"]["model"]["checkpoint"], dtype="bfloat16",
        tensor_parallel_size=1, seed=42, gpu_memory_utilization=.85,
        max_model_len=128000, max_num_seqs=8, limit_mm_per_prompt={"image": 3},
        enable_prefix_caching=False, trust_remote_code=True)
    engine = llm.llm_engine
    schemas = load(P / "protocol/schemas_v6.json")
    save(root / "environment.json", dict(
        at=now(), job=job, node=node, gpu=torch.cuda.get_device_name(0),
        versions=versions, engine_config=str(engine.vllm_config), manifest=m,
        runtime_sha256=sha(P / "protocol/runtime_v6.json"), ready_seconds=time.monotonic()-start))
    completed = 0

    def call_batch(tasks):
        nonlocal completed
        active, answers = {}, {}
        cursor = 0
        last_heartbeat = 0
        phase_start = time.monotonic()
        while cursor < len(tasks) or active:
            while cursor < len(tasks) and len(active) < 8:
                if time.monotonic() > deadline - 120:
                    break
                t = tasks[cursor]
                cursor += 1
                row, rid = t["row"], t["id"]
                folder = root / rid
                assert not folder.exists()
                prep_start = time.monotonic()
                images = t.get("images", [])
                if t["kind"] == "solver":
                    inp = prepare_inputs_for_vllm(row["original_messages"], processor)
                    assert inp["prompt"] == row["original_chat_prompt"]
                    inp["prompt"] += row["prefix"] + t.get("suffix", "")
                else:
                    prompt = compact_prompt(t["prompt"])
                    messages = (build_mathv_prompt({"question": prompt}, lambda _: images, "MathVision")
                                if images else [dict(role="user", content=[dict(type="text", text=prompt)])])
                    inp = (prepare_inputs_for_vllm(messages, processor) if images else
                           dict(prompt=processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)))
                    assert inp["prompt"].endswith("<think>\n")
                    inp["prompt"] += "</think>\n\n"
                prepared = inp.get("multi_modal_data", {}).get("image", [])
                pixels = [hashlib.sha256(im.tobytes()).hexdigest() for im in prepared]
                sizes = [list(im.size) for im in prepared]
                if t["kind"] == "solver":
                    assert pixels == row["original_image_pixels"]
                    assert sizes == row["original_image_sizes"]
                structured = None
                if t["kind"] != "solver":
                    schema = deepcopy(schemas[t["kind"]])
                    if t["kind"] == "query":
                        schema["anyOf"][0]["properties"]["source_refs"]["items"] = {
                            "enum": [s["id"] for s in build_catalog(row["question"], row["prefix"])]}
                    structured = StructuredOutputsParams(json=schema)
                params = SamplingParams(
                    **cfg["helper_recipe"], max_tokens=t["cap"], seed=row["seed"],
                    stop_token_ids=[], ignore_eos=False, structured_outputs=structured)
                save(folder / "input.json", dict(
                    at=now(), id=rid, family_id=row["family_id"], item_id=row["item_id"],
                    kind=t["kind"], prompt=inp["prompt"], pixels=pixels, sizes=sizes,
                    preprocessing_seconds=time.monotonic()-prep_start,
                    images=[row["image"]] if t["kind"] == "solver" else images,
                    prefix_sha256=row["prefix_sha256"], sampling=cfg["helper_recipe"],
                    cap=t["cap"], seed=row["seed"], job=job, schema=structured.json if structured else None))
                engine.add_request(rid, inp, params)
                active[rid] = dict(task=t, started=time.monotonic(), latest=None)
            if not active:
                break
            try:
                updates = engine.step()
            except BaseException as exc:
                for rid, data in active.items():
                    out = data["latest"].outputs[0] if data["latest"] else None
                    save(root / rid / "interrupted.json", dict(
                        at=now(), reason="ENGINE_ERROR", error=repr(exc),
                        raw=out.text if out else "", tokens=list(out.token_ids) if out else []))
                raise
            for output in updates:
                data = active[output.request_id]
                data["latest"] = output
                if not output.finished:
                    continue
                generated = output.outputs[0]
                rid = output.request_id
                folder = root / rid
                g = dict(
                    at=now(), id=rid, tokens=len(generated.token_ids),
                    generated_token_ids=list(generated.token_ids),
                    raw_decoded_response=generated.text, prompt_token_ids=list(output.prompt_token_ids),
                    prompt_tokens=len(output.prompt_token_ids),
                    visual_tokens=sum(t == 151655 for t in output.prompt_token_ids),
                    finish_reason=generated.finish_reason, stop_reason=generated.stop_reason,
                    cap_hit=generated.finish_reason == "length",
                    latency_seconds=time.monotonic()-data["started"],
                    job=job, node=node, seed=data["task"]["row"]["seed"])
                save(folder / "generation.json", g)
                save(folder / "result.json", dict(
                    input_sha256=sha(folder / "input.json"),
                    generation_sha256=sha(folder / "generation.json")))
                answers[rid] = dict(g, generation_path=str(folder / "generation.json"))
                del active[rid]
                completed += 1
                print("COMPLETE", m["id"], rid, g["tokens"], g["finish_reason"], flush=True)
            if time.monotonic() > deadline - 30:
                engine.abort_request(list(active))
                for rid, data in active.items():
                    out = data["latest"].outputs[0] if data["latest"] else None
                    save(root / rid / "interrupted.json", dict(
                        at=now(), reason="ALLOCATION_DEADLINE",
                        raw=out.text if out else "", tokens=list(out.token_ids) if out else []))
                raise TimeoutError("Preserved active continuations at allocation deadline")
            if time.monotonic() - last_heartbeat > 60:
                save(root / "heartbeats" / f"{time.time_ns()}.json", dict(
                    at=now(), completed=completed, seconds=time.monotonic()-start,
                    active={rid: len(x["latest"].outputs[0].token_ids) if x["latest"] else 0
                            for rid, x in active.items()},
                    remaining_tasks=len(tasks)-cursor))
                last_heartbeat = time.monotonic()
        if cursor != len(tasks):
            raise TimeoutError("Allocation admission boundary; unstarted tasks remain")
        save(root / "timings" / f"{time.time_ns()}.json", dict(
            at=now(), task_ids=[t["id"] for t in tasks],
            elapsed_seconds=time.monotonic()-phase_start,
            output_tokens=sum(g["tokens"] for g in answers.values())))
        return answers

    def task(row, name, kind="solver", cap=64, **kwargs):
        return dict(id=f"{row['item_id']}_{name}", row=row, kind=kind, cap=cap, **kwargs)

    try:
        if m["mode"] == "technical":
            pairs = [call_batch([task(r, f"replay_{rep}") for r in work]) for rep in ("a", "b")]
            comparisons = []
            for row in work:
                a = pairs[0][row["item_id"]+"_replay_a"]
                b = pairs[1][row["item_id"]+"_replay_b"]
                comparisons.append(dict(
                    item_id=row["item_id"],
                    exact=a["generated_token_ids"] == b["generated_token_ids"],
                    input_token_identity=a["prompt_token_ids"] == b["prompt_token_ids"]))
            save(root / "replay.json", dict(cases=comparisons))
            assert len(comparisons) == 8 and all(c["exact"] and c["input_token_identity"] for c in comparisons)
            prior_controls = load(P / "raw/technical_v5/controls.json")
            save(root / "controls.json", dict(prior_controls, reused_from="technical_v5",
                                              reason="Query prompt/schema/runtime component unchanged"))

        # Reuse every unchanged QUERY result, including rejected queries.
        oldstates = {r["item_id"]: load(P / "raw/technical_v5/states" / (r["item_id"]+".json")) for r in work}
        allowed_reuse = load(P / "protocol/helper_reuse_v6.json")["files"]
        def reused_generation(path):
            assert path in allowed_reuse and sha(path) == allowed_reuse[path]
            return dict(load(path), generation_path=path)
        qout = {r["item_id"]+"_query": reused_generation(oldstates[r["item_id"]]["query_generation"]) for r in work}
        states = {}
        eligible = []
        for row in work:
            item = row["item_id"]
            g = qout[item+"_query"]
            q = parse_record(g["raw_decoded_response"])
            catalog = build_catalog(row["question"], row["prefix"])
            ok, reason = validate_query(q, catalog)
            compiled = compile_query(q, catalog) if ok else None
            states[item] = dict(item_id=item, family_id=row["family_id"], query=q,
                                query_valid=ok, query_reason=reason, compiled_query=compiled,
                                query_generation=g["generation_path"])
            if ok and q["status"] == "QUERY":
                eligible.append(row)
        locations = call_batch([
            task(r, "locate", "locate", 2048,
                 prompt=helper_prompt(r, "locate", states[r["item_id"]]["compiled_query"]),
                 images=[r["image"]]) for r in eligible])
        readjobs = []
        for row in work:
            item = row["item_id"]
            state = states[item]
            g = locations.get(item+"_locate")
            raw_address = parse_record(g["raw_decoded_response"]) if g else None
            try:
                address = normalize_address(raw_address)
            except ValueError:
                address = None
            with Image.open(row["image"]) as image:
                w, h = image.size
            ok = validate_address(address, w, h)
            state.update(raw_address=raw_address, address=address, address_valid=ok,
                         locator_generation=g["generation_path"] if g else None)
            views = (render_views(row["image"], address, P / "data/views" / m["id"] / item)
                     if ok else dict(paths=[row["image"]], status="INVALID_OR_NOT_ATTEMPTED", transforms=[]))
            state["views"] = views
            reads, aliases = read_plan(row["image"], row in eligible, ok, views["paths"])
            state["read_aliases"] = aliases
            for arm, images in reads.items():
                if arm in ("G", "Q", "QI"):
                    continue
                readjobs.append(task(row, arm+"_read", "read", 2048, images=images,
                    prompt=helper_prompt(row, arm, state["compiled_query"],
                                         address if arm in ("QIA", "QGL") else None)))
            save(P / "data/source_packets" / m["id"] / f"{item}.json", dict(
                item_id=item, family_id=row["family_id"], image=row["image"],
                question=row["question"], prefix=row["prefix"], query=state["compiled_query"],
                raw_query=state["query"], query_valid=state["query_valid"],
                raw_address=raw_address, address=address, views=views, readouts_hidden=True, finals_hidden=True))
        readouts = call_batch(readjobs)
        for row in work:
            for arm in ("G", "Q", "QI"):
                path = oldstates[row["item_id"]]["readouts"][arm]["generation_path"]
                if path:
                    readouts[row["item_id"]+"_"+arm+"_read"] = reused_generation(path)
        solver_jobs = []
        for row in work:
            item = row["item_id"]
            state = states[item]
            records, metadata = {}, {}
            for arm in ("G", "Q", "QI", "QIA", "QGL"):
                source = state["read_aliases"].get(arm, arm)
                g = readouts.get(item+"_"+source+"_read")
                record = parse_record(g["raw_decoded_response"]) if g else None
                records[arm] = record
                metadata[arm] = dict(value=record, valid=valid_readout(record),
                    generation_path=g["generation_path"] if g else None,
                    alias_of=source if source != arm else None)
            physical, logical = continuation_plan(item, records)
            state.update(readouts=metadata, logical_continuations=logical)
            cap = 256 if m["mode"] == "technical" else 81920
            for rid, suffix in physical.items():
                solver_jobs.append(dict(id=rid, row=row, kind="solver", cap=cap, suffix=suffix))
            save(root / "acquisition" / f"{item}.json", state)
        save(root / "continuation_plan.json", dict(
            families=len(work), logical_slots=len(work)*6,
            requests=[dict(id=t["id"], item_id=t["row"]["item_id"], cap=t["cap"],
                           suffix_sha256=hashlib.sha256(t["suffix"].encode()).hexdigest())
                      for t in solver_jobs]))
        cout = call_batch(solver_jobs)
        for item, state in states.items():
            state["continuation_paths"] = {
                arm: cout[rid]["generation_path"] for arm, rid in state["logical_continuations"].items()}
            save(root / "states" / f"{item}.json", state)
        save(root / "exit.json", dict(at=now(), status="COMPLETE", completed=completed,
            seconds=time.monotonic()-start, peak_gpu_bytes=torch.cuda.max_memory_allocated(),
            families=len(work), main_pilot=m["mode"] == "main"))
    except BaseException as exc:
        save(root / "error.json", dict(at=now(), error=repr(exc),
            traceback=traceback.format_exc(), completed=completed, seconds=time.monotonic()-start))
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    run(parser.parse_args().manifest)
