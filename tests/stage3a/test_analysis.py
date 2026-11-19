from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/stage3a/analyze_scoring.py"
SPEC = importlib.util.spec_from_file_location("stage3a_analyze_scoring", SCRIPT)
assert SPEC and SPEC.loader
ANALYSIS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYSIS)


class FigureRenderingTest(unittest.TestCase):
    def test_temporal_curve_uses_nested_bootstrap_interval(self) -> None:
        facts = [
            {
                "base_problem_id": "1",
                "CE_controlled": 1.0,
                "CE": 1.2,
                "sham_shift": 0.2,
                "D_original": 0.8,
                "D_counterfactual": -0.4,
                "D_sham": 0.6,
                "evidence_type": "local_numeric",
            }
        ]
        temporal = {
            "common_checkpoint_curve": [
                {
                    "relative_to_e0_tokens": -8,
                    "CE_controlled": {
                        "mean": 1.0,
                        "mean_bootstrap_ci": {"ci_low": 0.5, "ci_high": 1.5},
                    },
                }
            ]
        }
        rollouts = [
            {
                "base_problem_id": "1",
                "condition": condition,
                "first_entity_or_fact_statement": "original_fact",
                "continuation_text": "test continuation",
            }
            for condition in ("original", "counterfactual", "sham")
        ]
        with tempfile.TemporaryDirectory(dir=Path.cwd() / "workspace") as directory:
            previous = ANALYSIS.FIGURES
            ANALYSIS.FIGURES = Path(directory)
            try:
                ANALYSIS.make_figures(facts, temporal, rollouts, {"matched_rows": []})
                self.assertTrue((ANALYSIS.FIGURES / "temporal_sensitivity_curve.png").is_file())
            finally:
                ANALYSIS.FIGURES = previous


if __name__ == "__main__":
    unittest.main()
