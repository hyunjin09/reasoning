"""Validate already-reviewed semantic/sham assets against current native geometry."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from visual_reasoning.stage3b7.roi import cell_darkness, choose_matched_irrelevant, fixed_ring, map_changed_pixels_to_tokens


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_assets(row, prompt, source):
    if source not in row["facts"]:
        raise ValueError("Source missing from inventory")
    if digest(row["asset_metadata"]) != row["asset_metadata_sha256"]:
        raise ValueError("Asset metadata hash changed")
    meta = json.loads(Path(row["asset_metadata"]).read_text())
    native = np.array(Image.open(row["image"]).convert("RGB"))
    fact = row["facts"][source]
    roi = fact.get("roi_xyxy",fact.get("roi"))
    x0,y0,x1,y1 = roi
    h,w = native.shape[:2]
    if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h):
        raise ValueError("ROI out of image")
    mask = np.zeros((h,w),dtype=bool)
    mask[y0:y1,x0:x1] = True
    temporal, rows, cols = prompt["visual_mapping"]["merged_grid_shape"]
    visual = prompt["visual_token_indices"]
    if temporal != 1 or len(visual) != rows*cols:
        raise ValueError("Unexpected native visual geometry")
    target = map_changed_pixels_to_tokens(mask,merged_rows=rows,merged_cols=cols)
    ring = fixed_ring(target,merged_rows=rows,merged_cols=cols,radius=1)
    irrelevant,audit = choose_matched_irrelevant(target_local=target,excluded_local=ring,
        darkness_by_cell=cell_darkness(native,merged_rows=rows,merged_cols=cols))
    if len(target) != len(irrelevant) or set(irrelevant) & set(ring):
        raise ValueError("Invalid matched irrelevant source")
    geometry = dict(source_roi_xyxy=roi,target_positions=[visual[i] for i in target],
                    irrelevant_positions=[visual[i] for i in irrelevant],irrelevant_audit=audit)
    if row["prior_stage"] == "4a":
        names = dict(O="OO", C="AO" if source == "A" else "OB", S=source+"_sham")
    elif row["prior_stage"] == "3c9r":
        names = dict(O="O", C="C", S="O_sham")
    else:
        names = dict(O="O", C="C_"+source, S="S_"+source)
    if any(name not in meta["paths"] for name in names.values()):
        return dict(**geometry,matched_controls=False,images={"O":row["image"]},
                    image_sha256={"O":digest(row["image"])},control_unavailable_reason="No matched semantic/sham source pair")
    paths = {condition: str(Path(meta["paths"][name]).resolve()) for condition,name in names.items()}
    roots = [Path.cwd().resolve(), Path("/data/dataset")]
    if not all(any(Path(p).is_relative_to(root) for root in roots) for p in paths.values()):
        raise ValueError("Control path outside allowed roots")
    old_hashes = meta.get("asset_sha256", meta.get("image_sha256", meta.get("automatic_validation",{}).get("sha256",{})))
    for condition,name in names.items():
        if name not in old_hashes or digest(paths[condition]) != old_hashes[name]:
            raise ValueError("Reviewed control hash changed")
    arrays = {k:np.array(Image.open(p).convert("RGB")) for k,p in paths.items()}
    if not all(a.shape == native.shape for a in arrays.values()) or not np.array_equal(arrays["O"],native):
        raise ValueError("Original/control pixels do not match native geometry")
    paths["O"] = row["image"]
    for condition in ("C","S"):
        if not np.array_equal(arrays[condition][~mask],native[~mask]):
            raise ValueError("Control changes pixels outside reviewed ROI")
        if np.array_equal(arrays[condition],native):
            raise ValueError("Control is identical to original pixels")
    return dict(**geometry,matched_controls=True,images=paths,image_sha256={k:digest(v) for k,v in paths.items()},
                original_asset_native_pixels_exact=True,edits_outside_roi_exact=True)
