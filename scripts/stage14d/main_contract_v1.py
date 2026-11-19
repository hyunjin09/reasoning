"""CPU input/release contract for the frozen scientific inventory.

No scheduler, CUDA imports, or executable launch entry point. The validated
technical adapter supplies the runtime path after explicit main release.
"""
from scripts.stage14d.design import enforce_release, fingerprint


def release_main(release, manifest_sha256, inventory):
    enforce_release(release)
    if release.get('manifest_sha256') != manifest_sha256:
        raise ValueError('Approval is not bound to this immutable manifest')
    if release.get('scientific_call_ceiling') != len(inventory):
        raise ValueError('Physical attempt ceiling must match exact eligible inventory')
    if not 1 <= release.get('concurrency', 0) <= 8:
        raise ValueError('Concurrency outside authorized range')
    if not all(r['executable'] for r in inventory):
        raise ValueError('Inapplicable row cannot enter execution inventory')


def exact_model_payload(row, native_input, native_generation, anchor, tokenizer):
    """Return only unexpanded token IDs; caller supplies original processed image.

    Compare vLLM output.prompt_token_ids to expected expanded IDs before scoring.
    Metadata dictionaries, E*, references, gold, and stratum never enter payload.
    Caller verifies pinned file hashes before passing these deserialized values.
    """
    n = row['prefix_tokens']
    prefix = list(native_generation['generated_token_ids'][:n])
    if prefix != anchor['prefix_generated_token_ids'] or fingerprint(prefix) != row['prefix_ids_sha256']:
        raise ValueError('Saved native prefix changed')
    if tokenizer.decode(prefix, skip_special_tokens=True) != anchor['prefix_text']:
        raise ValueError('Native prefix decoded bytes changed')
    directive = tokenizer.encode(row['directive'], add_special_tokens=False).ids
    if directive != row['directive_ids']:
        raise ValueError('Directive tokenization changed')
    chat_ids = tokenizer.encode(native_input['chat_prompt'], add_special_tokens=False).ids
    expected = list(native_generation['prompt_token_ids']) + prefix + directive
    if len(expected) != row['processed_prompt_tokens'] or len(expected) + row['max_tokens'] > 128000:
        raise ValueError('Context contract changed')
    return dict(unexpanded_input_ids=chat_ids+prefix+directive, expected_processed_input_ids=expected)


def admit_scientific(task_id, rows, admitted, remaining_reserved_seconds, minimum_safe_seconds):
    if task_id not in rows or not rows[task_id]['executable'] or task_id in admitted:
        raise ValueError('Unmanifested, inapplicable or already attempted continuation')
    if remaining_reserved_seconds < minimum_safe_seconds:
        raise ValueError('Hold before new request: safe allocation/budget reservation unavailable')

