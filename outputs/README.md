# Selected research reports

Git contains only the explicitly allowlisted consolidated reports and the
output-local Stage14D-0 phase memory. Raw generations, source images, tensor
captures, binary tables, figures, run receipts and frozen operational manifests
are artifact data and remain outside Git.

An explicit exception is the [Thinking math failure result bundle](thinking_math_failure_audit/v1/shared/README.md):
reviewed CSV/JSON tables, small sharded per-case records/source metadata,
selected human-readable casebook traces and a vector figure are published for
cross-server analysis. Bulk caches and duplicate inventories remain local.

Links in these historical reports may point to excluded artifacts. This is
intentional; a clone is not a complete experiment archive. The self-contained
research history under `reports/` preserves report text and source hashes.

Before resuming any stage on a different server, securely transfer the required
artifact subtree from the existing archive, verify the stage's hashes, and map
local dataset/model paths under the new access policy. Never regenerate sealed
artifacts merely because they were not included in Git. See the root README.

To publish another small summary, review it and add its exact path and parent
directories to `.gitignore`'s allowlist; do not broadly unignore `outputs/`.
