import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from visual_reasoning.stage3a.edits import build_polyline_conditions, build_text_conditions, validate_edit_conditions


class EditTest(unittest.TestCase):
    def test_text_edit_and_sham_only_change_declared_roi(self) -> None:
        with tempfile.TemporaryDirectory(dir="workspace") as temporary:
            tmp_path = Path(temporary)
            source = tmp_path / "source.png"
            image = Image.new("RGB", (100, 60), "white")
            image.save(source)
            spec = {
                "roi_xyxy": [20, 15, 80, 45],
                "original_text": "3 cm",
                "counterfactual_text": "5 cm",
                "font_size": 18,
                "text_color": [20, 30, 40],
                "background_color": [255, 255, 255],
                "text_anchor": [4, 4],
            }
            paths = build_text_conditions(source, tmp_path / "conditions", spec)
            checks = validate_edit_conditions(paths, spec["roi_xyxy"])
            self.assertTrue(checks["passed"])
            self.assertTrue(checks["dimensions_match"])
            self.assertTrue(checks["counterfactual_outside_roi_exact"])
            self.assertTrue(checks["sham_outside_roi_exact"])
            self.assertGreater(checks["counterfactual_diff_pixels_inside_roi"], 0)
            self.assertGreater(checks["sham_diff_pixels_inside_roi"], 0)

    def test_text_edit_can_infer_a_gray_background_from_the_roi(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.png"
            image = Image.new("RGB", (80, 50), (137, 137, 137))
            draw = ImageDraw.Draw(image)
            draw.text((22, 14), "40", fill="black")
            image.save(source)
            spec = {
                "roi_xyxy": [18, 10, 48, 32],
                "original_text": "40",
                "counterfactual_text": "30",
                "font_size": 13,
                "text_anchor": [4, 2],
                "background_mode": "roi_bright_median",
            }
            paths = build_text_conditions(source, root / "conditions", spec)
            rendered = np.asarray(Image.open(paths["counterfactual"]).convert("RGB"))
            self.assertTrue(np.array_equal(rendered[10, 18], np.array([137, 137, 137])))
            self.assertTrue(validate_edit_conditions(paths, spec["roi_xyxy"])["passed"])

            original = np.asarray(Image.open(paths["original"]))
            counterfactual = np.asarray(Image.open(paths["counterfactual"]))
            self.assertFalse(np.array_equal(original, counterfactual))

    def test_polyline_sham_and_counterfactual_stay_inside_plot_roi(self) -> None:
        with tempfile.TemporaryDirectory(dir="workspace") as temporary:
            tmp_path = Path(temporary)
            source = tmp_path / "source.png"
            image = Image.new("RGB", (120, 100), "white")
            image.save(source)
            spec = {
                "roi_xyxy": [10, 10, 110, 90],
                "original_points": [[12, 88], [108, 12]],
                "counterfactual_points": [[12, 70], [60, 70], [108, 12]],
                "line_color": [0, 0, 0],
                "line_width": 2,
                "background_color": [255, 255, 255],
                "preserve_boxes": [[80, 75, 105, 88]],
            }
            paths = build_polyline_conditions(source, tmp_path / "conditions", spec)
            checks = validate_edit_conditions(paths, spec["roi_xyxy"])
            self.assertTrue(checks["passed"])
            self.assertTrue(checks["counterfactual_outside_roi_exact"])
            self.assertTrue(checks["sham_outside_roi_exact"])
            original = np.asarray(Image.open(paths["original"]))
            counterfactual = np.asarray(Image.open(paths["counterfactual"]))
            self.assertTrue(np.array_equal(original[75:88, 80:105], counterfactual[75:88, 80:105]))

    def test_color_mask_curve_edit_preserves_noncurve_grid_pixels(self) -> None:
        with tempfile.TemporaryDirectory(dir="workspace") as temporary:
            tmp_path = Path(temporary)
            source = tmp_path / "source.png"
            image = Image.new("RGB", (80, 80), "white")
            pixels = np.asarray(image).copy()
            pixels[40, 10:70] = [210, 210, 210]
            pixels[20:60, 30] = [42, 162, 187]
            Image.fromarray(pixels).save(source)
            spec = {
                "roi_xyxy": [5, 5, 75, 75],
                "original_points": [[30, 20], [30, 59]],
                "counterfactual_points": [[10, 60], [70, 20]],
                "line_color": [42, 162, 187],
                "line_width": 2,
                "background_color": [255, 255, 255],
                "erase_mode": "color_mask",
                "erase_color": [42, 162, 187],
                "erase_tolerance": 0,
            }
            paths = build_polyline_conditions(source, tmp_path / "conditions", spec)
            counterfactual = np.asarray(Image.open(paths["counterfactual"]))
            self.assertTrue(np.array_equal(counterfactual[40, 50], [210, 210, 210]))


if __name__ == "__main__":
    unittest.main()
