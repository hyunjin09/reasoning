import unittest
from PIL import Image, ImageDraw
from scripts.stage14c.line_source import read_vertical_orders


class PixelSourceTests(unittest.TestCase):
    def test_three_observed_orders_not_intersection_count(self):
        im=Image.new('RGB',(400,400),'white');d=ImageDraw.Draw(im)
        d.line([(0,340),(200,60),(399,280)],fill='blue',width=5)
        d.line([(0,210),(200,210),(399,60)],fill='red',width=5)
        self.assertEqual(read_vertical_orders(im)['orders'],['below','above','below'])

    def test_absent_color_is_not_fabricated(self):
        with self.assertRaises(ValueError):read_vertical_orders(Image.new('RGB',(400,400),'white'))

    def test_ambiguous_middle_not_accepted(self):
        im=Image.new('RGB',(400,400),'white');d=ImageDraw.Draw(im)
        d.line([(0,50),(399,350)],fill='blue',width=5)
        d.line([(0,350),(399,50)],fill='red',width=5)
        with self.assertRaises(ValueError):read_vertical_orders(im)


if __name__=='__main__':unittest.main()
