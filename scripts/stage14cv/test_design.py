import itertools
import unittest

from scripts.stage14cv.design import (
    ORIGINAL_PREFIX, CONTRACT_SUFFIX, parse_original, render_r1, parse_r1,
    render_r2, parse_r2, remove_conflict, select_expansion,
)


class DesignTest(unittest.TestCase):
    def test_all_source_orders_survive_both_formats(self):
        for orders in itertools.product(('above', 'below'), repeat=3):
            text = ORIGINAL_PREFIX + '; '.join(
                f'At the {p} vertex blue is {v} red'
                for p, v in zip(('left', 'middle', 'right'), orders)) + '.'
            ledger = parse_original(text)
            self.assertEqual(tuple(ledger['blue_relative_to_red'].values()), orders)
            self.assertEqual(parse_r1(render_r1(ledger)), ledger)
            self.assertEqual(parse_r2(render_r2(ledger)), ledger)

    def test_early_source_wordings(self):
        for relation in ('above', 'below'):
            ledger = parse_original(ORIGINAL_PREFIX +
                f'Blue is {relation} red at the left, middle, and right vertices.')
            self.assertEqual(set(ledger['blue_relative_to_red'].values()), {relation})
        ledger = parse_original(ORIGINAL_PREFIX +
            'Blue is below red at the left vertex, above red at the middle vertex, and above red at the right vertex.')
        self.assertEqual(list(ledger['blue_relative_to_red'].values()), ['below', 'above', 'above'])

    def test_unknown_or_inferred_content_is_rejected(self):
        good = ORIGINAL_PREFIX + 'Blue is above red at the left, middle, and right vertices.'
        for text in [good + ' There are zero intersections.',
                     good.replace('straight', 'curved'), good.replace('above', 'level with'),
                     good.replace('left, middle, and right vertices.', 'middle, left, and right vertices.')]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_original(text)

    def test_r1_cannot_silently_add_fields_or_flip_order(self):
        import json
        ledger = parse_original(ORIGINAL_PREFIX + 'Blue is below red at the left, middle, and right vertices.')
        value = json.loads(render_r1(ledger)); value['answer'] = 0
        with self.assertRaises(ValueError): parse_r1(json.dumps(value))
        value.pop('answer'); value['ordered_vertices'] = ['right', 'middle', 'left']
        with self.assertRaises(ValueError): parse_r1(json.dumps(value))

    def test_c1_is_exact_suffix_deletion(self):
        question = 'How many times do the blue and red lines touch each other?'
        self.assertEqual(remove_conflict(question + CONTRACT_SUFFIX), question)
        for prompt in [question, question + CONTRACT_SUFFIX + ' hint',
                       question + CONTRACT_SUFFIX + CONTRACT_SUFFIX]:
            with self.assertRaises(ValueError): remove_conflict(prompt)

    def test_second_historical_answer_contract(self):
        question = 'Count the intersection points where the blue and red lines meet.'
        suffix = ' Put your answer in curly brackets, e.g., {2}.'
        self.assertEqual(remove_conflict(question + suffix), question)
        with self.assertRaises(ValueError): remove_conflict(question + suffix + CONTRACT_SUFFIX)

    def test_source_only_selection_is_order_invariant_and_disjoint(self):
        ids = [f'BlindTest:{i}' for i in range(300)]
        old = ids[:100]
        chosen = select_expansion(ids, old)
        self.assertEqual(len(chosen), 100)
        self.assertFalse(set(old) & set(chosen))
        self.assertEqual(chosen, select_expansion(list(reversed(ids)), list(reversed(old))))
        with self.assertRaises(ValueError): select_expansion(ids[:-1], old)
        with self.assertRaises(ValueError): select_expansion(ids, old[:-1] + ['not-in-cohort'])


if __name__ == '__main__':
    unittest.main()
