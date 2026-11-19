import json,tempfile,unittest
from pathlib import Path
from scripts.stage14e.common import save,update
class Storage(unittest.TestCase):
 def test_receipts_stay_immutable_and_progress_keeps_history(self):
  with tempfile.TemporaryDirectory(dir='outputs/stage14e_acquisition_development/v1/audit') as d:
   p=Path(d)/'state.json';save(p,{'n':1})
   with self.assertRaises(FileExistsError):save(p,{'n':2})
   update(p,{'n':3});self.assertEqual(json.loads(p.read_text()),{'n':3})
   snapshots=list((p.parent/'snapshot_history').glob('*.json'));self.assertEqual(len(snapshots),1)
   self.assertEqual(json.loads(snapshots[0].read_text()),{'n':1})
if __name__=='__main__':unittest.main()
