import unittest

from scripts.stage14a.sampling import stratified_order, confirm, map_versions


class SourceSelectionTest(unittest.TestCase):
    def test_order_preserves_all_rows_and_hash_order_within_strata(self):
        rows = [dict(family_id=str(i), category='a' if i < 8 else 'b') for i in range(12)]
        result = stratified_order(rows, ['category'], 'test|')
        self.assertEqual(result, stratified_order(rows[::-1], ['category'], 'test|'))
        self.assertEqual(len({r['family_id'] for r in result}), 12)
        self.assertEqual(sum(r['category'] == 'a' for r in result[:6]), 4)

    def test_confirmation_exact_size_and_no_duplicates(self):
        rows = [dict(family_id=str(i), category=i % 3) for i in range(19)]
        selected = confirm(rows, 7, ['category'], 'confirm|')
        self.assertEqual(len(selected), 7)
        self.assertEqual(len({r['family_id'] for r in selected}), 7)
        with self.assertRaises(ValueError):
            confirm(rows, 20, ['category'], 'confirm|')

    def test_version_identity_uses_problem_not_colliding_sample_namespace(self):
        rows = [dict(problem_index='1', sample_index='1', problem_version=v, answer='D')
                for v in ['Text Dominant', 'Text Only']]
        groups = map_versions(rows)
        self.assertEqual(set(groups['1']), {'Text Dominant', 'Text Only'})
        with self.assertRaises(ValueError):
            map_versions(rows + [rows[0]])
        with self.assertRaises(ValueError):
            map_versions(rows + [dict(problem_index='1', problem_version='Vision Only', answer='B')])


if __name__ == '__main__':
    unittest.main()
