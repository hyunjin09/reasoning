import csv
import tempfile
import unittest
from pathlib import Path

from scripts.thinking_math_failure_audit.publish_results import csv_parts, trace_features


class PublicationTests(unittest.TestCase):
    def test_multiline_unicode_csv_roundtrip_across_parts(self):
        with tempfile.TemporaryDirectory(dir='workspace') as tmp:
            folder=Path(tmp);source=folder/'source.csv'
            with source.open('w',newline='') as f:
                writer=csv.writer(f)
                writer.writerows([['id','question'],['1','α, "quoted"\nsecond line'],['2','β'*25],['3','last']])
            parts=csv_parts(source,folder/'parts',limit=100)
            self.assertGreater(len(parts),1)
            restored=bytearray()
            for i,path in enumerate(parts):
                data=path.read_bytes()
                restored.extend(data if i==0 else data.split(b'\r\n',1)[1])
            self.assertEqual(bytes(restored),source.read_bytes())
            self.assertTrue(all(p.stat().st_size<=100 for p in parts))

    def test_trace_features_keep_counts_without_copying_match_cache(self):
        source={'task_id':'case','lexical_flags':{'assumption_language':[],
            'image_unavailable_statement':[{'start':3,'end':9,'quote':"I can't see the image",'context':'surrounding text'}]}}
        exported=trace_features(source)
        self.assertEqual(exported['image_unavailable_statement_count'],1)
        self.assertEqual(exported['strict_named_image_denial_count'],1)
        self.assertEqual(exported['assumption_language_count'],0)
        self.assertNotIn('lexical_flags',exported)
        self.assertIn('context',source['lexical_flags']['image_unavailable_statement'][0])


if __name__=='__main__':unittest.main()
