#!/usr/bin/env bash
set -euo pipefail

cd /data/projects/hyunjin/MLLM/reasoning_steps
export PYTHONPATH=code:.

.venv/bin/python -c 'import json; assert json.load(open("outputs/stage3c9/audit/mechanical_validation.json"))["passed"]'

.venv/bin/torchrun --standalone --nproc_per_node=4 \
  scripts/stage3c9/run_source_sensitivity.py \
  --manifest outputs/stage3c9/cohort/primary_manifest.jsonl \
  --output-dir outputs/stage3c9/phase_a_source/raw \
  --mode primary --resume

.venv/bin/python scripts/stage3c9/analyze_source_sensitivity.py \
  --raw-root outputs/stage3c9/phase_a_source/raw \
  --manifest outputs/stage3c9/cohort/primary_manifest.jsonl \
  --role primary

.venv/bin/torchrun --standalone --nproc_per_node=4 \
  scripts/stage3c9/run_checkpoint_rescue.py \
  --manifest outputs/stage3c9/cohort/primary_manifest.jsonl \
  --source-classification outputs/stage3c9/phase_b_checkpoint/source_sensitive_events.jsonl \
  --output-dir outputs/stage3c9/phase_b_checkpoint/raw \
  --mode primary --resume

.venv/bin/python scripts/stage3c9/analyze_checkpoint_rescue.py \
  --raw-root outputs/stage3c9/phase_b_checkpoint/raw \
  --manifest outputs/stage3c9/cohort/primary_manifest.jsonl \
  --w8-source outputs/stage3c9/phase_a_source/w8_source_sensitivity.jsonl \
  --w16-source outputs/stage3c9/phase_a_source/w16_source_sensitivity.jsonl \
  --role primary

.venv/bin/torchrun --standalone --nproc_per_node=4 \
  scripts/stage3c9/run_lifetime.py \
  --manifest outputs/stage3c9/cohort/primary_manifest.jsonl \
  --classification outputs/stage3c9/phase_b_checkpoint/checkpoint_classification.json \
  --output-dir outputs/stage3c9/phase_c_lifetime/raw --resume

.venv/bin/python scripts/stage3c9/analyze_lifetime.py \
  --raw-root outputs/stage3c9/phase_c_lifetime/raw \
  --manifest outputs/stage3c9/cohort/primary_manifest.jsonl \
  --classification outputs/stage3c9/phase_b_checkpoint/checkpoint_classification.json \
  --span-results outputs/stage3c9/phase_b_checkpoint/event_span_rescue.jsonl

if .venv/bin/python -c 'import json,sys; sys.exit(0 if json.load(open("outputs/stage3c9/phase_d_routes/gate.json"))["run_phase_d"] else 1)'; then
  .venv/bin/torchrun --standalone --nproc_per_node=4 \
    scripts/stage3c9/run_routes.py \
    --manifest outputs/stage3c9/cohort/primary_manifest.jsonl \
    --pair-manifest outputs/stage3c9/phase_d_routes/route_pair_manifest.jsonl \
    --output-dir outputs/stage3c9/phase_d_routes/raw \
    --mode primary --resume
  .venv/bin/python scripts/stage3c9/analyze_routes.py \
    --raw-root outputs/stage3c9/phase_d_routes/raw --role primary
fi

.venv/bin/python scripts/stage3c9/materialize_gated_outputs.py
.venv/bin/python scripts/stage3c9/analyze_enrichment.py
.venv/bin/python scripts/stage3c9/assemble_analysis.py
.venv/bin/python scripts/stage3c9/make_figures.py
.venv/bin/python scripts/stage3c9/write_reports.py
.venv/bin/python scripts/stage3c9/validate_outputs.py
.venv/bin/pytest -q tests/stage3c9
