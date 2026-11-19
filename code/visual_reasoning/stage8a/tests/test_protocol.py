import pytest

from visual_reasoning.stage8a.protocol import generation_parameters, runtime_rank, source_partition, termination_status


def test_two_slurm_tasks_use_their_single_bound_device():
    env = {"SLURM_JOB_ID": "114923", "SLURM_NTASKS": "2", "SLURM_PROCID": "1"}
    assert runtime_rank(env, visible_devices=1, allocation="114923") == 1
    with pytest.raises(ValueError, match="one Slurm-bound"):
        runtime_rank(env, visible_devices=2, allocation="114923")
    with pytest.raises(ValueError, match="allocation"):
        runtime_rank({**env, "SLURM_JOB_ID": "different"}, visible_devices=1, allocation="114923")


def test_out_of_range_or_missing_rank_cannot_duplicate_the_cohort():
    env = {"SLURM_JOB_ID": "114923", "SLURM_NTASKS": "2", "SLURM_PROCID": "2"}
    with pytest.raises(ValueError, match="rank"):
        runtime_rank(env, visible_devices=1, allocation="114923")
    with pytest.raises(ValueError, match="rank"):
        runtime_rank({k:v for k,v in env.items() if k != "SLURM_PROCID"}, visible_devices=1, allocation="114923")


def test_visual_reasoning_and_nonvisual_competitors_are_disjoint_and_exhaustive():
    p = source_partition(prompt_length=7, sequence_length=11, visual_positions=[2,3,4])
    assert p["V"] == [2,3,4]
    assert p["N"] == [0,1,5,6,7,8,9,10]
    assert p["R"] == [7,8,9,10]
    assert sorted(p["V"]+p["N"]) == list(range(11))
    with pytest.raises(ValueError, match="prompt"):
        source_partition(prompt_length=7, sequence_length=11, visual_positions=[8])
    with pytest.raises(ValueError, match="duplicate"):
        source_partition(prompt_length=7, sequence_length=11, visual_positions=[2,2])


def test_eos_and_length_limit_are_separate_observations():
    assert termination_status([1,2,9], eos_ids=[9], cap=3) == {"normal_eos":True,"at_length_cap":True,"truncated":False,"tokens":3}
    assert termination_status([1,2,3], eos_ids=[9], cap=3)["truncated"]
    with pytest.raises(ValueError, match="neither"):
        termination_status([1,2], eos_ids=[9], cap=3)


def test_user_protocol_explicitly_overrides_checkpoint_temperature_default():
    p=generation_parameters()
    assert p == {"do_sample":True,"temperature":0.6,"top_p":0.95,"top_k":20,"repetition_penalty":1.0}
