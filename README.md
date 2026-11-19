# Reasoning steps: visual evidence acquisition in VLMs

Research code and records for reasoning-conditioned visual retrieval, evidence
handoff, evidence-supply bottlenecks and acquisition methods on multimodal math.

Start with the [key findings](reports/research_history_key_findings_2026-11-19.md).
The [complete history](reports/research_history_all_stages_2026-11-19.md) contains
99 stages/branches/audits, detailed reports and provenance. Research is paused
after Stage14E2; cloning or moving servers does not authorize new experiments.

## What belongs in Git

| Shared in Git | Kept local / transferred separately |
|---|---|
| `code/`, `scripts/`, `tests/`, shared infrastructure | `.venv/`, uv/pip caches, downloaded third-party repositories |
| `plan/`, phase memories and compact research state | Models, datasets, images, tensor captures, large tables |
| Selected consolidated reports and research histories | Raw `outputs/`, `runs/`, live `state/`, logs, job queues |
| Environment specifications and server setup templates | `ACCESS_POLICY.md`, `infra/gpu_policy.md`, `infra/gpu_scheduler.py`, `workspace/env_state.md` |

Outdated `piqd_agent_specs_v4/` (and the misspelled variant), `fix_AGENTS.md`,
credentials and temporary files are ignored. Historical PIQD source code remains
for provenance; the outdated standalone specification bundle is excluded.
`.gitignore` uses a root allowlist and exact output-document paths. Scientific
records retain exact bytes through `.gitattributes`; do not reformat sealed files.

## Set up each server

1. Clone the repository and create a short-lived branch for the work:

   ```bash
   git clone git@github.com:hyunjin09/reasoning.git
   cd reasoning
   git switch -c work/<server>-<stage>-<task>
   ```

2. Read `AGENTS.md`. Initialize **new machine-local files** from `infra/templates/`:
   `ACCESS_POLICY.md`, `infra/gpu_policy.md`, `infra/gpu_scheduler.py`, and
   `workspace/env_state.md`. Fill approved paths, cluster topology and limits
   before agent file access or scheduling. Do not overwrite existing local
   policies on an already configured server. The scheduler example preserves
   the existing implementation but has empty topology tables and refuses to run
   until configured; it is not a universal cluster adapter.

3. Use project-local environments; do not copy `.venv` between machines:

   ```bash
   uv venv --python 3.12 .venv
   uv pip install --python .venv/bin/python -r requirements.txt
   ```

   For the recent vLLM experiments, use a separate environment after checking
   driver/platform compatibility and the active stage's exact runtime contract:

   ```bash
   uv venv --python 3.12 .venv/official_eval
   uv pip install --python .venv/official_eval/bin/python \
     -r infra/requirements-inference-vllm.txt
   ```

   These are observed top-level package pins, not a universal transitive lock or
   a guarantee of cross-hardware bitwise replay. The historical stage receipts
   govern exact reproduction. Some early stages use other Torch/Transformers
   stacks; do not silently rerun them with this recent inference stack.
   No environment is installed and no model is loaded by the Git setup itself.

4. Check `workspace/research_plan.md`, the relevant phase memory, and the active
   approved plan. Historical node names, absolute paths and old job IDs in source
   scripts/reports are not current infrastructure instructions. Some launchers
   require a machine-local path/node adapter; inspect before executing them.

5. Locate datasets and pinned models under the new local access policy. Restore
   the required artifact subtrees from the existing research archive separately.
   A Git clone alone cannot resume artifact-dependent experiments. Preserve
   frozen IDs, source hashes, seeds, labels and prior outputs; verify hashes
   before continuing. Do not rerun or relabel missing artifacts as a shortcut.
   Keep archive location and restore verification in local environment state.

6. Run the active stage's bounded CPU checks and required scheduled runtime
   validation. Do not run the entire historical suite blindly: some tests need
   excluded artifacts, a specific stack, scheduler configuration or GPUs.

## Work safely across servers

- Begin with `git status` and `git fetch origin`. Update a clean `main` with
  `git pull --ff-only`, then create a task branch. Use one branch per server/task.
- Commit and push small completed changes. Move work to another server by
  fetching/checking out that branch, not by copying `.git` or environments.
- Use a pull request or reviewed merge for shared `main`; never force-push it.
  If `main` moved, reconcile changes on the task branch before merging.
- A Git branch does not coordinate GPU jobs or reserve a scientific cohort.
  Assign a single execution owner/run ID before launching, check active stage
  state, and avoid duplicate inference across servers. Preserve immutable raw
  outputs in the artifact archive and publish only compact result/state updates.
- Update phase memory at research-action boundaries. Resolve concurrent edits
  explicitly; never silently replace another server's results or resource ledger.
- Keep local policies/paths/queues untracked. Before every commit:

  ```bash
  git add <explicit-reviewed-paths>
  python3 infra/check_git_payload.py
  git diff --cached --stat
  git diff --cached
  git commit -m "<type>: <purpose>"
  git push -u origin <task-branch>
  ```

The payload guard checks staged paths, file sizes, symlinks, binary content and
recognizable credential patterns without printing secret values. It is a
backstop, not a substitute for reviewing the diff. Do not use `git add -f` for
large artifacts or machine-local configuration.

## Repository map

- `code/`: reusable implementations and historical experimental components.
- `scripts/`: stage runners, analysis, validation and reporting code.
- `tests/`: CPU and stage-specific checks; additional tests live beside code.
- `infra/`: shared orchestration helpers, payload guard and local setup templates.
- `plan/`: approved plans, protocols, amendments and execution checklists.
- `workspace/phase_memory/`: stage findings, constraints, decisions and status.
- `reports/`: research-history entry points; some historical index targets are local.
- `outputs/`: only selected consolidated documents; see `outputs/README.md`.

No license is inferred for the project or for third-party benchmark/model data.
Follow original dataset/model terms when accessing or transferring artifacts.
