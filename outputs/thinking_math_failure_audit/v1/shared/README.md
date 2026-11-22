# Portable Thinking math failure results

Start with the [report](../../../../reports/thinking_math_failure_audit/thinking_failure_analysis_20261122.md) and [14-case casebook](../../../../reports/thinking_math_failure_audit/casebook_20261122.md). This Git bundle supports further analysis of the completed retrospective on another server, without model inference or access to the original server.

## Included

- `all_thinking_records/part-*.csv`: all **13,568** outcome/provenance rows. Each part has the same header. Concatenating the data rows reproduces the original CSV exactly; the original checksum is in `manifest.json`.
- `trace_features.csv`: all **13,568** per-call trace feature rows, including literal-flag counts, strict named-image-denial counts, boundaries, text lengths and provenance. The bulky full match cache stays local. Broad image-denial quotes, Unicode offsets and contexts are retained in the adjacent `text_reliance_screen_candidates.csv`; other raw-text inspection requires the archive.
- `source_metadata/part-*.jsonl`: **8,768** unique source/condition records, including the saved question, benchmark gold, choices, subject and source metadata. Join using `identity + "::" + condition`; image and evidence conditions can have different metadata. Seeds share source records.
- Adjacent `../*.csv` / selected `../*.json`: complete main failure index, question-type/source-feature tables, evidence transitions, modality and repeated-seed sensitivities, historical evidence tables, lexical-screen summaries and validation/provenance records.
- `../case_traces/*.md`: the **14 complete selected Thinking responses**, with the full pre- and post-`</think>` text.
- `../figures/question_types_and_structure.svg`: portable vector figure. Original PNG/PDF exports remain in the artifact archive.

Main native scope is **7,768 r0 outputs**, with **2,303 scored wrong** and **26 unscorable**. Repeated seeds and E* followups are separately identified. CSV empty cells mean missing/not applicable, not false or zero. Nested arrays/objects are JSON strings in CSV fields. Source IDs, family IDs, versions and seeds must remain distinct in new analyses.

## Verify after cloning

From the repository root, using the server's project-local Python environment:

```bash
.venv/bin/python -m scripts.thinking_math_failure_audit.publish_results --verify
```

This check uses only the standard library and the published files. It verifies checksums, the lossless CSV reconstruction, record counts, unique task IDs and source/condition joins. It performs no inference and needs no GPUs or original raw archive.

For example, read all outcomes with the standard library:

```python
import csv
from pathlib import Path

bundle = Path("outputs/thinking_math_failure_audit/v1/shared")
rows = []
for part in sorted((bundle / "all_thinking_records").glob("part-*.csv")):
    with part.open(newline="") as stream:
        rows.extend(csv.DictReader(stream))
```

The analysis and publication code is in `scripts/thinking_math_failure_audit/`. `plot_results.py` redraws the vector figure from the shared numeric tables with the project's NumPy/Matplotlib environment.

## Archive still required for deeper source review

The original benchmark images, all 13,568 raw generations/token arrays/input receipts, bulk trace-screen caches, original Stage14A/B artifacts and the full historical semantic-annotation archive are **not** in this bundle. Dataset/model contents and server-local policies remain excluded from Git.

Absolute paths retained in source metadata and historical reports are provenance from the original server, not instructions for a new server. Map dataset/artifact locations under that server's access policy. The selected complete traces and tables above work from the Git clone; original-image inspection and regeneration of the retrospective from raw receipts require the separately transferred archive. Do not rerun model inference to replace missing sealed records.

`failure_inventory.jsonl` is omitted because it duplicates outcomes/source records and screening data. The full unsharded CSV, context-rich trace cache and bulk input-receipt list remain local. These packaging choices do not omit outcomes, change labels, or introduce new causal classifications.

The manifest covers numeric tables, shards and selected traces. This README and SVG are explanatory/rendered additions. Stage14E2 remains paused; this bundle authorizes analysis only.
