"""Bound generation to the user's96-review interim gate; never score effects."""
from scripts.stage7a.common import read_json, sha
from scripts.stage7a_bench.native_migration_v3 import pending_rows


def bounded_shards(rows, completed_ids, target):
    ids = [row['event_id'] for row in rows]
    if (target != 96 or len(rows) != 200 or len(set(ids)) != 200 or
            not completed_ids or completed_ids != ids[:len(completed_ids)] or
            len(completed_ids) >= target or
            any(row['benchmark'] != 'mathvision_wild' or row['condition'] != 'photo' for row in rows)):
        raise ValueError('The interim release must preserve the frozen MathWild photo prefix and96-item gate')
    remaining = rows[len(completed_ids):target]
    return [remaining[rank::4] for rank in range(4)]


def select_gate_rows(root, rows, selection, run_id):
    if selection.get('status') != 'FROZEN_USER_AMENDED_MATHWILD_GATE96':
        raise ValueError('Explicit frozen user-amended gate selection required')
    for reference in (selection['amendment'], selection['continuation']):
        path = (root / reference['path']).resolve()
        if not path.is_relative_to(root.resolve()) or sha(path) != reference['sha256']:
            raise ValueError('Gate authority or continuation evidence changed')
    packet = read_json(root / selection['continuation']['path'])
    # Reuse all completed-prefix response/source hash checks before selecting
    # a bounded shard. No completed result is copied or regenerated.
    pending_rows(root, rows, packet, packet['continuation_run_id'])
    shards = bounded_shards(rows, packet['completed_event_ids'], selection['target_reviewed_items'])
    records = selection['shards']
    if len(records) != 4 or len({r['run_id'] for r in records}) != 4:
        raise ValueError('Exactly four distinct frozen shard identities required')
    for expected, record in zip(shards, records):
        if record['event_ids'] != [row['event_id'] for row in expected]:
            raise ValueError('Shard would skip, repeat or exceed the frozen interim prefix')
    matches = [i for i, record in enumerate(records) if record['run_id'] == run_id]
    if len(matches) != 1:
        raise ValueError('Run is not one of the four gate shards')
    return shards[matches[0]]
