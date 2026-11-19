import copy
import unittest
from scripts.stage12br.protocol import select_families, validity, gate, authorize_manifest


class ProtocolTests(unittest.TestCase):
    def test_pathology_never_excludes_unique_outcome(self):
        r = validity(True, True, False, False)
        self.assertTrue(r['TECHNICALLY_VALID'])
        self.assertTrue(validity(True, True, True, False)['cap_after_outcome'])
        self.assertFalse(validity(True, False, True, False)['TECHNICALLY_VALID'])
        self.assertTrue(validity(True, False, True, False)['TRUNCATED_BEFORE_OUTCOME'])
        with self.assertRaises(AssertionError):
            validity(True, True, False, True)

    def test_gate_boundaries_and_input_precedence(self):
        rows = {a: [validity(True, True, False, False) for _ in range(12)] for a in 'ENO'}
        for rr in rows.values():
            rr[0] = validity(True, False, True, False)
            rr[1] = validity(True, False, False, False)
        self.assertEqual(gate(rows)['decision'], 'VALIDITY_REPAIRED')
        rows['E'][1] = validity(True, False, True, False)
        self.assertEqual(gate(rows)['decision'], 'SCOREABILITY_FAIL')
        rows['N'][0] = validity(False, False, False, False)
        self.assertEqual(gate(rows)['decision'], 'INPUT_INTEGRITY_FAIL')

    def test_selection_only_identity_and_type(self):
        rows = [dict(item_id=str(i), family_id=f'f{i}', answer_type='multiple_choice' if i < 20 else 'open_ended') for i in range(61)]
        excluded = [str(i) for i in range(4)] + [str(i) for i in range(20, 28)]
        selected, _ = select_families(rows, excluded)
        altered = [dict(r, subject='changed', difficulty=-1, correctness=False, token_length=0) for r in reversed(rows)]
        self.assertEqual(selected, select_families(altered, excluded)[0])
        self.assertEqual(len(selected), 12)
        self.assertFalse(set(selected) & set(excluded))
        self.assertEqual(sum(next(r for r in rows if r['item_id'] == i)['answer_type'] == 'multiple_choice' for i in selected), 5)

    def test_only_frozen_validation_tasks_authorized(self):
        tasks = [dict(task_id=str(i)) for i in range(36)]
        frozen = dict(tasks=tasks, config_sha256='cfg')
        manifest = dict(frozen=True, phase='validation', rows=tasks[:18], config_sha256='cfg')
        authorize_manifest(manifest, frozen)
        for change in [dict(phase='main'), dict(rows=[dict(task_id='old')]), dict(config_sha256='changed'), dict(rows=tasks[:18] * 2)]:
            with self.assertRaises(AssertionError):
                authorize_manifest(dict(manifest, **change), frozen)


if __name__ == '__main__':
    unittest.main()
