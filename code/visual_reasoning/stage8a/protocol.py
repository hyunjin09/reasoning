"""Small execution and source-coordinate guards for the approved 2B stage."""


def generation_parameters():
    return dict(do_sample=True, temperature=0.6, top_p=0.95, top_k=20, repetition_penalty=1.0)


def runtime_rank(env, *, visible_devices, allocation):
    if env.get("SLURM_JOB_ID") != str(allocation):
        raise ValueError("Must use the authorized allocation")
    if int(visible_devices) != 1:
        raise ValueError("Each task must see exactly one Slurm-bound GPU")
    try:
        rank, count = int(env["SLURM_PROCID"]), int(env["SLURM_NTASKS"])
    except (KeyError, ValueError) as exc:
        raise ValueError("Missing or invalid Slurm rank") from exc
    if count != 2 or not 0 <= rank < count:
        raise ValueError("Expected a rank in the two-task step")
    return rank


def source_partition(*, prompt_length, sequence_length, visual_positions):
    prompt, total = int(prompt_length), int(sequence_length)
    visual = [int(x) for x in visual_positions]
    if len(set(visual)) != len(visual):
        raise ValueError("Visual indices contain a duplicate")
    if not visual or total < prompt or any(x < 0 or x >= prompt for x in visual):
        raise ValueError("Visual positions must be inside the nonempty prompt")
    return {"V": sorted(visual), "N": sorted(set(range(total))-set(visual)),
            "R": list(range(prompt,total)), "sink": [0]}


def termination_status(token_ids, *, eos_ids, cap):
    ids = list(token_ids)
    if not ids or len(ids) > int(cap):
        raise ValueError("Invalid generated sequence length")
    eos = ids[-1] in set(eos_ids)
    at_cap = len(ids) == int(cap)
    if not eos and not at_cap:
        raise ValueError("Generation reached neither EOS nor length cap")
    return {"normal_eos": eos, "at_length_cap": at_cap, "truncated": not eos, "tokens": len(ids)}
