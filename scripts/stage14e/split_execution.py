"""Reconstruct exactly the sealed helper-to-solver transport, never source labels."""
import hashlib
from scripts.stage14e.evaluation_contracts import continuation_plan


def frozen_plan(item_id, acquisition, logical_rows):
    physical, assignments = continuation_plan(item_id, acquisition['readouts'])
    given = {r['arm']: r for r in logical_rows if r['item_id'] == item_id}
    assert set(given) == set(assignments)
    for arm, assignment in assignments.items():
        assert given[arm]['physical_id'] == assignment['physical_id']
        assert given[arm]['status'] == assignment['status']
        suffix = physical[assignment['physical_id']]
        assert hashlib.sha256(suffix.encode()).hexdigest() == given[arm]['suffix_sha256']
    return physical, assignments


def physical_order(physical):
    return sorted(physical, key=lambda k: hashlib.sha256(('stage14e-arm-order-v1|' + k).encode()).hexdigest())
