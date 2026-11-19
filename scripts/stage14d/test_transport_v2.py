import json
import unittest
from scripts.stage14d.transport_v2 import TechnicalExtension, control_message


class NamedTransportTests(unittest.TestCase):
    def test_control_message_uses_registered_name_not_callable(self):
        message=control_message(dict(prompt_len=4,image_positions=[1],off=True))
        self.assertEqual(message[0],'stage14d_configure')
        self.assertEqual(json.loads(json.dumps(message))[1][0]['image_positions'],[1])
        self.assertTrue(callable(getattr(TechnicalExtension,message[0])))

    def test_collection_has_a_distinct_registered_method(self):
        self.assertTrue(callable(getattr(TechnicalExtension,'stage14d_collect')))


if __name__=='__main__':unittest.main()
