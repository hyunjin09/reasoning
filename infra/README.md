# Shared infrastructure and local configuration

Read the [repository setup guide](../README.md) and this server's
`ACCESS_POLICY.md` before using these tools.

`harness_state.py`, `workflow_hooks.py`, dataset utilities and the Git payload
validator are shared source. The actual `gpu_policy.md` and `gpu_scheduler.py`
are machine-local and ignored. Configure them from `templates/` for the current
cluster; never assume another server's partitions, memory caps or GPU count.
The scheduler example requires explicit topology configuration before any action.

GPU work must follow the configured scheduler/access policy. Bounded CPU work
and long CPU jobs follow local guidance. No scheduler command in this README
submits or authorizes an experiment.

For dataset discovery, supply only allowed local roots to
`check_dataset_cache.py`. Record results in the inventory. Downloads require an
explicitly writable destination under the current local access policy and must
occur one dataset at a time. Neither old dataset paths nor historical report
text grants write permission on a new server.

Before committing, run `python3 infra/check_git_payload.py` against the staged
index. Large raw artifacts and live scheduler state belong outside Git.
