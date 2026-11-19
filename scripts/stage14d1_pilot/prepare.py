"""Materialize unchanged runtime cohort and prospective technical controls."""
import hashlib
import json
from pathlib import Path

from scripts.stage14d1.contracts import safe_payload
from scripts.stage14d1.contracts_v3 import SCHEMAS
from scripts.stage14d1_pilot.common import *
from scripts.stage14d1_pilot.provenance import QUERY_SCHEMA, build_catalog

CONTROLS = [
    ("positive_marker", "QUERY", "Which letter labels the point immediately left of the diamond?",
     "I need the label of the point immediately left of the diamond. It has not been read yet."),
    ("positive_rows", "QUERY", "The diagram has four rows. What symbol occupies row four?",
     "The next required image fact is the symbol in row four, whose identity is still unknown."),
    ("positive_edges", "QUERY", "How many edges meet at the marked vertex in the graph?",
     "The connectivity of the marked vertex must be read from the graph before computing."),
    ("positive_roman", "QUERY", "The diagram has regions I, II and III. What shape occupies region III?",
     "The shape in region III is unknown and needs a visual reading."),
    ("negative_sum", "NONE", "Add eight and two using these given numbers.",
     "Only addition remains. No image information is required."),
    ("negative_given", "NONE", "The requested cell is explicitly stated to be green. Name its color.",
     "The color is already supplied by the question; no visual lookup is needed."),
    ("negative_algebra", "NONE", "Solve x + 7 = 10 from the supplied equation.",
     "The entire equation is in the text. The next operation is symbolic subtraction."),
    ("negative_sides", "NONE", "A rectangle has width six and height nine. Compute its area.",
     "Both required lengths are supplied in text. The remaining step is multiplication."),
]


def main():
    original = rows(OLD / "inference/families.jsonl")
    assert len(original) == len({r["family_id"] for r in original}) == 72
    catalogs = {}
    for row in original:
        safe_payload(row)
        assert sha(row["image"]) == row["image_sha256"]
        assert hashlib.sha256(row["prefix"].encode()).hexdigest() == row["prefix_sha256"]
        catalogs[row["item_id"]] = build_catalog(row["question"], row["prefix"])
        for span in catalogs[row["item_id"]]:
            assert row[span["source"]][span["start"]:span["end"]] == span["text"]
    for name, source in [
        ("inference/families.jsonl", OLD / "inference/families.jsonl"),
        ("protocol/arm_manifest.jsonl", OLD / "protocol/arm_manifest.jsonl"),
        ("protocol/sampler_and_seeds.json", OLD / "protocol/sampler_and_seeds.json"),
        ("data/offline_source_manifest.jsonl", OLD / "data/selected_family_target_manifest.jsonl"),
    ]:
        path = P / name
        with path.open("xb") as f:
            f.write(source.read_bytes())
    config = load(RECOVERY / "protocol/runtime.json")
    config["runtime"]["v1_multiprocessing"] = 0
    config["caps"]["main_continuation"] = 81920
    config["protocol_version"] = "source_reference_v4"
    # An allocation deadline is the only operational timeout; do not truncate long
    # scientific generations with the old technical per-request timeout.
    config["timeout_seconds"] = None
    save(P / "protocol/runtime.json", config)
    save(P / "protocol/schemas.json", dict(SCHEMAS, query=QUERY_SCHEMA))
    save(P / "protocol/technical_controls.json", dict(
        at=now(), cases=[dict(id=i, expected=e, question=q, prefix=p, seed=1009000+k)
                         for k, (i, e, q, p) in enumerate(CONTROLS)],
        condition="Independent synthetic text-only query controls; not scientific families"))
    save(P / "data/source_catalogs.json", catalogs)
    save(P / "audit/cohort_identity.json", dict(
        at=now(), families=72, logical_arms=432, original_runtime_payload_sha256=sha(OLD / "inference/families.jsonl"),
        new_runtime_payload_sha256=sha(P / "inference/families.jsonl"),
        unchanged_images_prefixes_seeds=True, prior_gpu_seconds=PRIOR_GPU_SECONDS,
        ceiling_gpu_seconds=CEILING_GPU_SECONDS,
        remaining_gpu_seconds=CEILING_GPU_SECONDS-PRIOR_GPU_SECONDS,
        no_oracle_runtime_fields=True, no_new_model_calls=True))
    print("Prepared same72/432; source catalogs and independent controls frozen.")


if __name__ == "__main__":
    main()
