import unittest
from scripts.stage14b.review_v1 import response_scope, response_packet


class ReviewTests(unittest.TestCase):
    def test_thinking_scope_never_mines_reasoning(self):
        self.assertEqual(response_scope('reason 3</think>final 4', 'T'), 'final 4')
        self.assertEqual(response_scope('reason 3', 'T'), '')

    def test_extraction_packet_is_gold_blind(self):
        t = dict(task_id='x', model_key='I', prompt='question', condition='image')
        g = dict(raw_decoded_response='B', finish_reason='stop', tokens=1)
        r = dict(options=['one','two'], gold_answer='A', correct=True)
        p = response_packet(t, g, r, dict(answer='B'), 200)
        self.assertNotIn('gold_answer', p)
        self.assertNotIn('correct', p)
        self.assertEqual(p['scope_tail'], 'B')


if __name__ == '__main__':
    unittest.main()
