"""CPU guards shared by the Stage14D technical manifest and GPU worker."""


def kept_positions(seq_len, image_positions):
    image = set(image_positions)
    if not image or min(image) < 0 or max(image) >= seq_len:
        raise ValueError('Image key positions must be inside the original prompt')
    return [i for i in range(seq_len) if i not in image]


def block_decode(query_len, seq_len, prompt_len, enabled):
    if seq_len <= prompt_len or not enabled:
        return False
    if query_len != 1:
        raise ValueError('Only a single generated query is validated')
    return True


def admit_call(identity, admitted, allowed, ceiling, remaining_seconds):
    if identity in admitted or identity not in allowed or len(admitted) >= ceiling:
        raise ValueError('Duplicate, unmanifested or excess technical call')
    if remaining_seconds < 180:
        raise ValueError('Insufficient allocation time; stop before admitting a call')
    return True


def exact_prefix(prompt_ids, native_ids, boundary, directive_ids):
    if type(boundary) is not int or not 0 <= boundary <= len(native_ids):
        raise ValueError('Invalid original-token prefix boundary')
    return list(prompt_ids) + list(native_ids[:boundary]) + list(directive_ids)
