from __future__ import annotations

import unittest

import torch

from visual_reasoning.stage3b0.cache import clone_cache, patch_cache_positions, validate_cache_layout


class FakeLayer:
    def __init__(self, offset: float) -> None:
        values = torch.arange(1 * 2 * 6 * 3, dtype=torch.float32).reshape(1, 2, 6, 3) + offset
        self.keys = values.clone()
        self.values = values.clone() + 1000
        self.is_initialized = True


class FakeCache:
    def __init__(self, offsets=(0.0, 100.0)) -> None:
        self.layers = [FakeLayer(offset) for offset in offsets]

    def get_seq_length(self, layer_idx: int = 0) -> int:
        return int(self.layers[layer_idx].keys.shape[-2])


class CachePatchTests(unittest.TestCase):
    def test_validate_clone_and_patch_all_layers_on_sequence_axis(self) -> None:
        recipient = FakeCache()
        source = FakeCache((10_000.0, 20_000.0))
        diagnostic = validate_cache_layout(
            recipient,
            expected_layers=2,
            expected_kv_heads=2,
            expected_sequence_length=6,
            expected_head_dim=3,
        )
        self.assertEqual(diagnostic["tensor_shape"], [1, 2, 6, 3])
        self.assertEqual(diagnostic["sequence_axis"], 2)

        patched, audit = patch_cache_positions(recipient, source, [2, 4])
        self.assertEqual(audit["layers_patched"], [0, 1])
        for layer_index in range(2):
            self.assertTrue(
                torch.equal(
                    patched.layers[layer_index].keys[:, :, [2, 4], :],
                    source.layers[layer_index].keys[:, :, [2, 4], :],
                )
            )
            self.assertTrue(
                torch.equal(
                    patched.layers[layer_index].values[:, :, [2, 4], :],
                    source.layers[layer_index].values[:, :, [2, 4], :],
                )
            )
            self.assertTrue(
                torch.equal(
                    patched.layers[layer_index].keys[:, :, [0, 1, 3, 5], :],
                    recipient.layers[layer_index].keys[:, :, [0, 1, 3, 5], :],
                )
            )
        self.assertTrue(torch.equal(recipient.layers[0].keys, clone_cache(recipient).layers[0].keys))

    def test_patch_rejects_misaligned_shapes_and_positions(self) -> None:
        with self.assertRaisesRegex(ValueError, "shape"):
            patch_cache_positions(FakeCache(), FakeCache((0.0,)), [1])
        with self.assertRaisesRegex(ValueError, "inside"):
            patch_cache_positions(FakeCache(), FakeCache(), [6])


if __name__ == "__main__":
    unittest.main()
