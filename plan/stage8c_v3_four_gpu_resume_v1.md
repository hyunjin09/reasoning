# Stage8C v3: four-GPU operational resume

Explicit user amendment 2026-09-20T05:07:29.862968+00:00: cancel current run and resume using four node02
GPUs. The scientific plan and full FP32 regime remain unchanged.

Slurm118529 was cancelled after approximately21 minutes. Zero trajectories were
complete; two interrupted attempts (658 at gains1.00 and1.25) are preserved with
hashes and logs. There is no serialized token/KV/RNG checkpoint, so these two
restart from their original seeds. All512 frozen tasks remain to be completed.
No item replacement, extraction/generation change or scientific retuning.

Run one process per GPU, four workers with static task slices rank::4,16CPUs
and160G host memory (40G/requested GPU, within node02 policy), five-day ceiling.
The original manifests/config/scripts stay untouched; versioned entry points
change only worker count, output phase and finalization paths. New outputs go
under dev_four_v1; finish_dev_four reads exactly those512 receipts. Resources
release on batch exit. No concurrent old allocation or tmux allocation.

Development decisions remain frozen and unchanged. The global experiment is
still in development; test512 and secondary analyses remain conditional.
