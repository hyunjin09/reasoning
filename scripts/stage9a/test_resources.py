"""Resource guards for the availability-driven native coordinator."""
import gpu_scheduler as scheduler


def jobs():
    return dict(jobs=[dict(id=f"w{i}",status="queued",gpu_type="a6000",gpus=1,
        node="",mem="30G",cpus=4,exclude_nodes=["node07"],priority="medium",created_at=str(i)) for i in range(4)])


def capacity(free,own=0):
    return dict(remaining_user_slots=max(0,4-own),available_gpus={"a6000":sum(free.values())},
        available_node_gpus={n:dict(gpu_type="a6000",available=k,total=10) for n,k in free.items()})


def test_no_unhealthy_node07_fallback():
    assert scheduler.plan_jobs(jobs(),capacity(dict(node02=0,node03=0,node06=0,node07=5)))==[]


def test_available_capacity_and_maximum_four():
    plan=scheduler.plan_jobs(jobs(),capacity(dict(node02=2,node03=3,node06=0,node07=5),own=1))
    assert len(plan)==3 and sum(j["gpus"] for j in plan)+1==4
    assert all(j["node"] in {"node02","node03"} for j in plan)
