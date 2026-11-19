import unittest
from scripts.stage14c.source_identity import blind_identity, connected_components


class SourceIdentityTests(unittest.TestCase):
    def test_line_base_identity_ignores_rendering_and_answer(self):
        a = blind_identity('Line Plot Intersections', 'gt_2_image_17_thickness_2_resolution_384.png', {})
        b = blind_identity('Line Plot Intersections', 'gt_0_image_17_thickness_4_resolution_768.png', {'gt': 0})
        self.assertEqual(a, b)
        self.assertNotEqual(a, blind_identity('Line Plot Intersections', 'gt_2_image_18_thickness_2_resolution_384.png', {}))

    def test_geometry_ignores_style_but_keeps_scene(self):
        m = dict(center_1=[.1, .2], center_2=[.8, .7], diameter=.3, dpi=100)
        a = blind_identity('Touching Circles', 'uuid.png', m)
        self.assertEqual(a, blind_identity('Touching Circles', 'other.png', dict(m, dpi=200)))
        self.assertNotEqual(a, blind_identity('Touching Circles', 'other.png', dict(m, center_2=[.9,.7])))

    def test_subway_conservative_structure_not_count(self):
        links = [dict(start='A', end='B', color='red'), dict(start='A', end='C', color='blue')]
        a = blind_identity('Subway Connections', 'a.png', dict(connections=links))
        self.assertEqual(a, blind_identity('Subway Connections', 'b.png', dict(connections=links[::-1])))
        changed = [dict(start='A', end='D', color='red'), links[1]]
        self.assertNotEqual(a, blind_identity('Subway Connections', 'b.png', dict(connections=changed)))

    def test_missing_identity_fails_closed(self):
        with self.assertRaises(ValueError): blind_identity('Line Plot Intersections', 'uuid.png', {})
        with self.assertRaises((ValueError, KeyError)): blind_identity('Subway Connections', 'uuid.png', {})

    def test_transitive_aliases(self):
        self.assertEqual(connected_components(['a','b','c','d'], [('a','b'),('b','c')]), [['a','b','c'],['d']])


if __name__ == '__main__': unittest.main()
