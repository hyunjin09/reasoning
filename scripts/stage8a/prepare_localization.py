"""Freeze source/readout-eligible calibration requests before any causal score."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image
from transformers import AutoTokenizer

from visual_reasoning.stage3b7.roi import cell_darkness, choose_matched_irrelevant, fixed_ring, map_changed_pixels_to_tokens
from visual_reasoning.stage8a.events import divergent_readout


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--protocol", default="plan/stage8a_localization_protocol_v2.md")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    out = Path(args.output)
    assert not out.exists()
    tokenizer = AutoTokenizer.from_pretrained(config["model_checkpoint"], local_files_only=True)
    manifest = [json.loads(s) for s in Path(config["manifest"]).read_text().splitlines()]
    requests, unavailable = [], []
    for row in manifest:
        annotation = Path(f"outputs/stage8a/annotations/calibration/{row['base_id']}.json")
        if not annotation.exists():
            unavailable.append(dict(base_id=row["base_id"], reason="No eligible reviewed annotation"))
            continue
        event = json.loads(annotation.read_text())
        assert event["full_event_prefix_reviewed"] and event["source_identity_valid"]
        assert event["local_claim_correct"] and not event["attention_or_causal_effects_seen"]
        native = Path(event["native_dir"])
        for name, expected in event["native_artifact_sha256"].items():
            assert digest(native/name) == expected, name
        assert digest(event["asset_metadata"]) == event["asset_metadata_sha256"]
        meta = json.loads(Path(event["asset_metadata"]).read_text())
        prompt = json.loads((native/"input.json").read_text())
        tokens = [json.loads(s) for s in (native/"tokens.jsonl").read_text().splitlines()]
        assert [r["token_id"] for r in tokens[:event["prefix_length"]]] == event["prefix_token_ids"]
        history = tokenizer.decode(event["prefix_token_ids"], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        candidate = tokenizer.encode(history+event["counterfactual"], add_special_tokens=False)
        if candidate[:len(event["prefix_token_ids"])] != event["prefix_token_ids"]:
            unavailable.append(dict(base_id=row["base_id"], reason="Counterfactual changes native prefix tokenization"))
            continue
        try:
            readout = divergent_readout(event["prefix_token_ids"], event["evidence_token_ids"], candidate[len(event["prefix_token_ids"]):])
        except ValueError as exc:
            unavailable.append(dict(base_id=row["base_id"], reason=str(exc)))
            continue
        assert [r["token_id"] for r in tokens[:len(readout["prefix_token_ids"])]] == readout["prefix_token_ids"]
        source = event["source_id"]
        if row["prior_stage"] == "4a":
            names = dict(O="OO", C="AO" if source == "A" else "OB", S=source+"_sham")
        elif row["prior_stage"] == "3c9r":
            names = dict(O="O", C="C", S="O_sham")
        else:
            names = dict(O="O", C="C_"+source, S="S_"+source)
        if any(name not in meta["paths"] for name in names.values()):
            unavailable.append(dict(base_id=row["base_id"], reason="Matched source semantic/sham assets unavailable"))
            continue
        paths = {condition: str(Path(meta["paths"][name]).resolve()) for condition, name in names.items()}
        allowed = [Path.cwd().resolve(), Path("/data/dataset")]
        assert all(any(Path(path).is_relative_to(root) for root in allowed) for path in paths.values())
        prior_hashes = meta.get("asset_sha256", meta.get("image_sha256", meta.get("automatic_validation", {}).get("sha256", {})))
        for condition, name in names.items():
            assert name in prior_hashes and digest(paths[condition]) == prior_hashes[name], (row["base_id"], name, "reviewed_asset_hash")
        arrays = {k: np.array(Image.open(path).convert("RGB")) for k, path in paths.items()}
        native_image = np.array(Image.open(row["image"]).convert("RGB"))
        assert all(a.shape == native_image.shape for a in arrays.values())
        assert np.array_equal(arrays["O"], native_image)
        # Native O bytes remain the input; prior OO encoding may differ losslessly.
        paths["O"] = row["image"]
        fact = row["facts"][source]
        roi = fact.get("roi_xyxy", fact.get("roi"))
        x0, y0, x1, y1 = roi
        height, width = native_image.shape[:2]
        assert 0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height
        mask = np.zeros((height, width), dtype=bool)
        mask[y0:y1, x0:x1] = True
        for condition in ["C", "S"]:
            assert np.array_equal(arrays[condition][~mask], native_image[~mask]), (row["base_id"], condition, "outsideROI")
            assert not np.array_equal(arrays[condition], native_image)
        temporal, h, w = prompt["visual_mapping"]["merged_grid_shape"]
        visual = prompt["visual_token_indices"]
        assert temporal == 1 and len(visual) == h*w
        target = map_changed_pixels_to_tokens(mask, merged_rows=h, merged_cols=w)
        ring = fixed_ring(target, merged_rows=h, merged_cols=w, radius=1)
        irrelevant, irrelevant_audit = choose_matched_irrelevant(
            target_local=target, excluded_local=ring,
            darkness_by_cell=cell_darkness(native_image, merged_rows=h, merged_cols=w))
        assert len(irrelevant) == len(target) and not set(irrelevant) & set(ring)
        requests.append(dict(event_id=event["event_id"], base_id=row["base_id"], family_id=row["family_id"],
            example_id=row["example_id"], source_id=source, native_dir=str(native), annotation=str(annotation),
            annotation_sha256=digest(annotation), input_sha256=digest(native/"input.json"),
            original_value=event["readout"], counterfactual_value=event["counterfactual"], **readout,
            literal_prefix_length=event["prefix_length"], causal_prefix_length=len(readout["prefix_token_ids"]),
            images=paths, image_sha256={k: digest(v) for k, v in paths.items()},
            source_roi_xyxy=roi, visual_positions=visual, prompt_length=prompt["prompt_token_count"],
            image_grid_thw=prompt["image_grid_thw"], target_positions=[visual[i] for i in target],
            irrelevant_positions=[visual[i] for i in irrelevant], irrelevant_audit=irrelevant_audit,
            original_asset_native_pixels_exact=True, edits_outside_roi_exact=True,
            source_selection_used_attention=False, source_selection_used_causal_effects=False))
    assert len(requests) >= 4, "Insufficient independent reviewed calibration families"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(frozen_at=datetime.now(timezone.utc).isoformat(),
        protocol=args.protocol, protocol_sha256=digest(args.protocol),
        manifest_sha256=digest(config["manifest"]), requests=requests, unavailable=unavailable,
        individual_layers=list(range(28)), candidate_late_window_starts=list(range(14,25)),
        window_length=4, heads=list(range(16)), minimum_families=4), indent=2, allow_nan=False)+"\n")
    print(json.dumps(dict(requests=len(requests), unavailable=len(unavailable), output=str(out))))


if __name__ == "__main__":
    main()
