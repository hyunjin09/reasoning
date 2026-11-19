import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.stage12ws.common import save,sha
from scripts.stage12ws.interrupted import packet

class InterruptedTests(unittest.TestCase):
    def test_no_output_has_unknown_stop_and_preserves_input(self):
        with tempfile.TemporaryDirectory(dir='outputs/stage12ws/v1/audit') as tmp:
            root=Path(tmp);task={'task_id':'test_missing'};folder=root/'generations/test_missing'
            save(folder/'input.json',{'task':task})
            receipt={'input_path':str(folder/'input.json'),'input_sha256':sha(folder/'input.json')}
            with patch('scripts.stage12ws.interrupted.ROOT',root):
                value=packet(task,receipt)
                self.assertIsNone(value['cap_hit'])
                self.assertIsNone(value['tokens'])
                self.assertEqual(value['finish_reason'],'INTERRUPTED_NO_OUTPUT')
                self.assertFalse((folder/'generation.json').exists())
                save(folder/'generation.json',{'raw':'late output'})
                with self.assertRaises(AssertionError):packet(task,receipt)

if __name__=='__main__':unittest.main()
