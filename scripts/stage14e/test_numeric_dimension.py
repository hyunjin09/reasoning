import unittest
from scripts.stage14e.contracts_v2 import numeric_lexemes, validate_demand, build_catalog


class Dimensions(unittest.TestCase):
    def test_plain_and_latex_dimension_equivalent(self):
        self.assertEqual(numeric_lexemes('7-foot-by-7-foot floor'), numeric_lexemes('$7$-foot-by-$7$-foot floor'))

    def test_unitless_dimension(self):
        self.assertEqual(numeric_lexemes('3-by-4 grid'), {'3', '4'})

    def test_arithmetic_sign_preserved(self):
        self.assertIn('-7', numeric_lexemes('x-7'))
        self.assertIn('-7', numeric_lexemes('coordinate -7'))

    def test_unknown_magnitude_not_removed(self):
        self.assertEqual(numeric_lexemes('7-foot-by-99-foot'), {'7', '99'})

    def test_transport_accepts_dimension_but_rejects_new_number(self):
        catalog = build_catalog('Inspect the $7$-foot-by-$7$-foot floor.', '')
        q = dict(status='QUERY', need='NEW_VISUAL', target='floor', property='layout',
                 frame='7-foot-by-7-foot floor', source_refs=['Q000'], answer_value=None)
        self.assertTrue(validate_demand(q, catalog)[0])
        self.assertFalse(validate_demand(dict(q, frame='7-foot-by-99-foot floor'), catalog)[0])


if __name__ == '__main__':
    unittest.main()
