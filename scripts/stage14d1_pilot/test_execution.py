import unittest
from scripts.stage14d1_pilot.execution import continuation_plan, read_plan, remaining_budget


def reading(value):
    return dict(target="point label", read_value=value, supporting_source="marked point", uncertainty="certain")


class ExecutionContracts(unittest.TestCase):
    def test_none_keeps_generic_but_targeted_alias_native(self):
        physical, logical = continuation_plan("x", {"G": reading("A")})
        self.assertEqual(len(physical), 2)
        self.assertEqual(logical["QI"], logical["N"])
        self.assertNotEqual(logical["G"], logical["N"])

    def test_identical_payloads_reuse_only_physical_solver(self):
        physical, logical = continuation_plan("x", {"G": reading("A"), "QI": reading("A")})
        self.assertEqual(len(physical), 2)
        self.assertEqual(logical["G"], logical["QI"])

    def test_malformed_read_falls_back_without_fabricating_read(self):
        _, logical = continuation_plan("x", {"QI": {"read_value": "A"}})
        self.assertEqual(logical["QI"], logical["N"])

    def test_invalid_locator_keeps_query_reads_full_image(self):
        physical, aliases = read_plan("image.png", True, False, None)
        self.assertEqual(set(physical), {"G", "Q", "QI"})
        self.assertEqual(physical["Q"], [])
        self.assertEqual(aliases, {"QIA": "QI", "QGL": "QI"})

    def test_global_fallback_is_not_a_crop(self):
        physical, aliases = read_plan("image.png", True, True, ["image.png"])
        self.assertEqual(aliases, {"QGL": "QIA"})
        self.assertNotIn("QGL", physical)

    def test_local_keeps_original_global_and_crop(self):
        physical, aliases = read_plan("image.png", True, True, ["image.png", "crop.png"])
        self.assertEqual(physical["QGL"], ["image.png", "crop.png"])
        self.assertEqual(aliases, {})

    def test_no_query_runs_only_generic_read(self):
        physical, aliases = read_plan("image.png", False, False, None)
        self.assertEqual(physical, {"G": ["image.png"]})
        self.assertEqual(aliases, {})

    def test_budget_includes_allocated_and_outstanding_reservations(self):
        self.assertEqual(remaining_budget(2709, [600], [14400, 14400]), 25491)
        with self.assertRaises(ValueError):
            remaining_budget(2709, [600], [20000, 20000, 20000])


if __name__ == "__main__":
    unittest.main()
