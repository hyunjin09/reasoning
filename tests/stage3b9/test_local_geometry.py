import numpy as np

from visual_reasoning.stage3b9.local_geometry import fit_leave_one_out_bases, phase_b_condition_aliases


def test_phase_b_condition_aliases_selects_one_value_pair():
    assert phase_b_condition_aliases(3) == {
        "O": "O",
        "O_sham": "O_sham",
        "C": "C3",
        "C_sham": "C3_sham",
    }


def test_leave_one_out_basis_excludes_held_out_delta():
    deltas = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 10.0],
    ])
    fitted = fit_leave_one_out_bases(deltas)
    assert fitted[3][3].shape == (4, 3)
    assert np.allclose(fitted[3][3][3], 0.0)
    assert np.allclose(fitted[0][1].T @ fitted[0][1], np.eye(1))
