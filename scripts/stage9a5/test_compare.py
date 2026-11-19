import unittest
from scripts.stage9a5.compare import paired_contrast


class PairedContrastTest(unittest.TestCase):
    def rows(self, damage):
        return [dict(query_id=f'{i}_{q}', image_id=str(i), policy=p,
                     correct=True if p=='full' else not damage[i])
                for i in range(4) for q in ('color','shape') for p in ('full','t128')]

    def test_exact_paired_cancellation(self):
        a=self.rows([True,False,True,False])
        r=paired_contrast(a,list(reversed(a)),'t128')
        self.assertEqual(r['difference'],0)
        self.assertEqual(r['ci95'],[0,0])
        self.assertEqual(r['n_images'],4)

    def test_direction_and_cluster(self):
        r=paired_contrast(self.rows([True]*4),self.rows([False]*4),'t128')
        self.assertEqual(r['difference'],1)
        self.assertEqual(r['ci95'],[1,1])
        self.assertEqual(r['images_more_thinking_damage'],4)

    def test_missing_or_duplicate_rejected(self):
        a=self.rows([True]*4)
        with self.assertRaises(AssertionError):paired_contrast(a,a[:-1],'t128')
        with self.assertRaises(AssertionError):paired_contrast(a,a+[a[0]],'t128')


if __name__=='__main__':unittest.main()
