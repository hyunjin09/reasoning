"""Freeze annotated requests without inspecting passive or causal outcomes."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from transformers import AutoTokenizer

from visual_reasoning.stage8a.source_assets import source_assets, digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["discovery","confirmation"], required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--preflight", action="store_true", help="Input validation only; not an executable full-split freeze")
    args = parser.parse_args()
    config = json.loads(Path("outputs/stage8a/config/main_native_v1.json").read_text())
    tokenizer = AutoTokenizer.from_pretrained(config["model_checkpoint"],local_files_only=True)
    manifest = [json.loads(s) for s in Path(config["manifest"]).read_text().splitlines()]
    active_path = Path("outputs/stage8a/annotations/active_reviews_v1.json")
    active = json.loads(active_path.read_text())["overrides"] if active_path.exists() else {}
    requests, reviews, missing = [], [], []
    for row in manifest:
        if row["split"] != args.split:
            continue
        annotation = Path(active.get(row["base_id"],f"outputs/stage8a/annotations/main_v1/{row['base_id']}.json"))
        if not annotation.is_file():
            missing.append(row["base_id"])
            continue
        review = json.loads(annotation.read_text())
        native = Path(review["native_dir"])
        for name,h in review["native_artifact_sha256"].items():
            assert digest(native/name) == h, (native,name)
        prompt = json.loads((native/"input.json").read_text())
        for event in review["events"]:
            assert event["effects_blind"] and event["full_event_prefix_reviewed"]
            assert event["prefix_length"] >= 2
            request = dict(event_id=event["event_id"],base_id=row["base_id"],family_id=row["family_id"],
                split=args.split,label=event["label"],example_id=row["example_id"],source_id=event.get("source_id"),
                native_dir=str(native),annotation=str(annotation),annotation_sha256=digest(annotation),
                input_sha256=digest(native/"input.json"),prefix_token_ids=event["prefix_token_ids"],
                original_token_ids=event["evidence_token_ids"],original_value=event["readout"],
                visual_positions=prompt["visual_token_indices"],prompt_length=prompt["prompt_token_count"],image_grid_thw=prompt["image_grid_thw"],
                images={"O":row["image"]},image_sha256={"O":row["image_sha256"]},target_positions=None,irrelevant_positions=None,
                semantic_eligible=False,semantic_unavailable_reason="No reviewed matched source readout",local_claim_correct=event["local_claim_correct"],
                source_role=("unavailable" if event.get("source_id") is None else
                    "candidate_label_source" if event.get("source_binding_error") or event.get("source_type_binding_error") else "demanded_source"),
                demand_kind=event.get("demand_kind","fresh_visual_value" if event["label"]=="T" else "no_fresh_visual_demand"),
                literal_prefix_length=event["prefix_length"],source_selection_used_attention=False,source_selection_used_causal_effects=False)
            if event.get("source_id") is not None:
                request.update(source_assets(row,prompt,event["source_id"]))
                cf = event.get("counterfactual")
                if request["matched_controls"] and cf is not None and event["local_claim_correct"]:
                    history = tokenizer.decode(event["prefix_token_ids"],skip_special_tokens=False,clean_up_tokenization_spaces=False)
                    ids = tokenizer.encode(history+cf,add_special_tokens=False)
                    prefix = event["prefix_token_ids"]
                    if ids[:len(prefix)] != prefix:
                        reason = "Counterfactual retokenizes native prefix"
                    else:
                        candidate = ids[len(prefix):]
                        original = event["evidence_token_ids"]
                        common = min(len(candidate),len(original))
                        if not candidate or candidate[:common] == original[:common]:
                            reason = "Identical or strict-prefix readouts need a reviewed terminator"
                        else:
                            reason = None
                            request.update(semantic_eligible=True,counterfactual_token_ids=candidate,counterfactual_value=cf)
                    request["semantic_unavailable_reason"] = reason
                elif not request["matched_controls"]:
                    request["semantic_unavailable_reason"] = request["control_unavailable_reason"]
                elif not event["local_claim_correct"]:
                    request["semantic_unavailable_reason"] = "Native local claim incorrect; semantic contrast requires separate oriented review"
            request["lexical_prefix_last32"] = tokenizer.decode(event["prefix_token_ids"][-32:],skip_special_tokens=False,clean_up_tokenization_spaces=False)
            requests.append(request)
        reviews.append(dict(base_id=row["base_id"],annotation=str(annotation),sha256=digest(annotation),events=len(review["events"])))
    # Extra negative quotas are selected by frozen manifest order, not finish
    # order or effects. Unselected manually reviewed candidates stay preserved.
    selected, selection_exclusions = [], []
    extra_counts = {"nearby":0,"nonvisual":0}
    extra_bases = {"nearby":set(),"nonvisual":set()}
    demand_positions = {}
    for request in requests:
        if request["label"] == "T":
            demand_positions.setdefault(request["base_id"],[]).append(len(request["prefix_token_ids"]))
    for request in requests:
        if request["label"] == "nearby":
            distance=[len(request["prefix_token_ids"])-p for p in demand_positions.get(request["base_id"],[]) if 0 < len(request["prefix_token_ids"])-p <= 256]
            assert distance, (request["event_id"],"Nearby label lacks a T within256 preceding native tokens")
            request["distance_from_prior_T_tokens"] = min(distance)
    requests.sort(key=lambda r:(next(i for i,row in enumerate(manifest) if row["base_id"]==r["base_id"]),len(r["prefix_token_ids"])))
    for request in requests:
        label = request["label"]
        if label in extra_counts:
            if request["base_id"] in extra_bases[label]:
                selection_exclusions.append(dict(event_id=request["event_id"],reason="Extra control class already represented by an earlier reviewed query in this base"))
                continue
            if extra_counts[label] >= 12:
                selection_exclusions.append(dict(event_id=request["event_id"],reason="Beyond first12 eligible controls of this class in frozen manifest order"))
                continue
            extra_counts[label] += 1
            extra_bases[label].add(request["base_id"])
        selected.append(request)
    requests = selected
    if not args.preflight:
        assert not missing, "Complete semantic review required before main split freeze"
        assert 80 <= len(requests) <= 120, "Event yield outside approved target; document/resolve before execution"
    subset = [r["event_id"] for r in requests if r["label"] == "T" and r["semantic_eligible"]][:12]
    protocol = "plan/stage8a_main_measurement_protocol_v2.md"
    result = dict(at=datetime.now(timezone.utc).isoformat(),split=args.split,preflight_only=args.preflight,
        protocol=protocol,protocol_sha256=digest(protocol),manifest=config["manifest"],manifest_sha256=digest(config["manifest"]),
        requests=requests,reviewed_bases=reviews,missing_reviews=missing,causal_confirmation_subset=subset,
        selection_exclusions=selection_exclusions,extra_negative_quota=12,
        subset_rule="First12 eligibleT events in frozen manifest/annotation order, before effects",
        annotation_override_sha256=digest(active_path) if active_path.exists() else None,
        source_scope_note="For binding/type errors, the ROI is a visible candidate label source, not a certified source for the demanded entity. Raw target-relative VSD means targeted-ROI relative suppression; interpret source_role before any demanded-source claim.",
        source_sha256={str(Path(__file__)):digest(__file__),"code/visual_reasoning/stage8a/source_assets.py":digest("code/visual_reasoning/stage8a/source_assets.py")})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x") as f:
        f.write(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(dict(events=len(requests),semantic_eligible=sum(r["semantic_eligible"] for r in requests),reviewed_bases=len(reviews),missing=len(missing),preflight=args.preflight)))


if __name__ == "__main__":
    main()
