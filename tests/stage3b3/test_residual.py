from types import SimpleNamespace

import torch

from visual_reasoning.stage3b3.residual import (
    CurrentPositionResidualPatch,
    replace_current_position,
    valid_residual_patch_audit,
)


def test_residual_replacement_changes_only_current_sequence_position() -> None:
    output = torch.arange(24, dtype=torch.float32).reshape(1, 4, 6)
    donor = torch.full((1, 6), 99.0)

    patched, audit = replace_current_position(output, donor, position=2)

    assert torch.equal(patched[:, :2], output[:, :2])
    assert torch.equal(patched[:, 3:], output[:, 3:])
    assert torch.equal(patched[:, 2], donor)
    assert audit["positions_replaced"] == [2]
    assert audit["noncurrent_positions_changed"] == 0


def test_residual_replacement_preserves_tuple_outputs() -> None:
    hidden = torch.zeros((1, 3, 2))
    cache = object()

    patched, audit = replace_current_position((hidden, cache), torch.ones((1, 2)), position=1)

    assert isinstance(patched, tuple)
    assert patched[1] is cache
    assert torch.equal(patched[0][:, 1], torch.ones((1, 2)))
    assert audit["output_container"] == "tuple"


def test_patch_context_attaches_to_only_one_language_layer() -> None:
    layers = [torch.nn.Identity() for _ in range(3)]
    model = SimpleNamespace(
        model=SimpleNamespace(language_model=SimpleNamespace(layers=layers))
    )
    patch = CurrentPositionResidualPatch(
        model=model,
        layer_index=1,
        position=0,
        source_state=torch.ones((1, 2)),
    )

    with patch:
        assert torch.equal(layers[0](torch.zeros((1, 1, 2))), torch.zeros((1, 1, 2)))
        assert torch.equal(layers[1](torch.zeros((1, 1, 2))), torch.ones((1, 1, 2)))
        assert torch.equal(layers[2](torch.zeros((1, 1, 2))), torch.zeros((1, 1, 2)))

    assert len(patch.audit) == 1
    assert patch.audit[0]["layer_index"] == 1


def test_residual_patch_audit_requires_one_exact_layer_and_position() -> None:
    audit = [{
        "layer_index": 5,
        "positions_replaced": [17],
        "noncurrent_positions_changed": 0,
        "current_position_exact_source_match": True,
    }]

    assert valid_residual_patch_audit(audit, layer_index=5, position=17)
    assert not valid_residual_patch_audit(audit, layer_index=4, position=17)
