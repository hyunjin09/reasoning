# Selected research reports

Git contains only the explicitly allowlisted consolidated reports and the
output-local Stage14D-0 phase memory. Raw generations, source images, tensor
captures, binary tables, figures, run receipts and frozen operational manifests
are artifact data and remain outside Git.

Links in these historical reports may point to excluded artifacts. This is
intentional; a clone is not a complete experiment archive. The self-contained
research history under `reports/` preserves report text and source hashes.

Before resuming any stage on a different server, securely transfer the required
artifact subtree from the existing archive, verify the stage's hashes, and map
local dataset/model paths under the new access policy. Never regenerate sealed
artifacts merely because they were not included in Git. See the root README.

To publish another small summary, review it and add its exact path and parent
directories to `.gitignore`'s allowlist; do not broadly unignore `outputs/`.
