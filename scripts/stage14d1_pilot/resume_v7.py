"""CPU contracts for capacity-safe admission and immutable receipt reuse."""
import hashlib
from pathlib import Path
from scripts.stage14d1_pilot.common import load, sha


def admission_fits(active_reservations, candidate_reservation, token_capacity, max_active=8):
    values = [*active_reservations, candidate_reservation, token_capacity, max_active]
    if any(type(v) is not int or v <= 0 for v in values):
        return False
    return len(active_reservations) < max_active and sum(active_reservations) + candidate_reservation <= token_capacity


def completed_receipt(folder, row, suffix):
    folder = Path(folder)
    if not (folder/'result.json').exists():
        return None
    try:
        receipt = load(folder/'result.json')
        assert receipt['input_sha256'] == sha(folder/'input.json')
        assert receipt['generation_sha256'] == sha(folder/'generation.json')
        i, g = load(folder/'input.json'), load(folder/'generation.json')
        assert all(i[k] == row[k] for k in ('family_id','item_id','seed','prefix_sha256'))
        assert hashlib.sha256(row['prefix'].encode()).hexdigest() == row['prefix_sha256']
        assert i['kind'] == 'solver' and i['cap'] == 81920
        assert i['id'] == g['id'] == folder.name
        assert i['prompt'] == row['original_chat_prompt'] + row['prefix'] + suffix
        assert i['pixels'] == row['original_image_pixels'] and i['sizes'] == row['original_image_sizes']
        assert g['seed'] == row['seed']
        assert type(g['tokens']) is int and 0 <= g['tokens'] <= 81920
        assert g['tokens'] == len(g['generated_token_ids'])
        assert g['finish_reason'] in ('stop','length')
        assert g['cap_hit'] == (g['finish_reason'] == 'length')
        assert g['finish_reason'] != 'length' or g['tokens'] == 81920
    except (AssertionError, OSError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f'Invalid completed receipt: {folder}') from exc
    return str(folder/'generation.json')
