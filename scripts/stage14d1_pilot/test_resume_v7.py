"""Independent CPU tests for cache admission and immutable completed receipts.

All receipt contents are synthetic. Temporary files remain beneath the project
runs/stage14d1_pilot directory; no scientific generations are read.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.stage14d1_pilot.resume_v7 import admission_fits, completed_receipt


CAP = 81920
PROJECT = Path(__file__).resolve().parents[2]
TEMP_ROOT = PROJECT / "runs" / "stage14d1_pilot"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True), encoding="utf-8")


class AdmissionTests(unittest.TestCase):
    def test_empty_queue_accepts_a_full_solver_reservation(self):
        self.assertTrue(admission_fits([], CAP + 2048, 201152))

    def test_full_cap_reservations_prevent_eight_request_oversubscription(self):
        reservation = CAP + 2048
        self.assertTrue(admission_fits([reservation], reservation, 201152))
        self.assertFalse(admission_fits([reservation, reservation], reservation, 201152))
        self.assertFalse(admission_fits([reservation] * 7, reservation, 201152))

    def test_exact_fit_is_allowed_and_one_token_over_is_rejected(self):
        live = [CAP + 1000]
        candidate = CAP + 2000
        self.assertTrue(admission_fits(live, candidate, sum(live) + candidate))
        self.assertFalse(admission_fits(live, candidate, sum(live) + candidate - 1))
        self.assertTrue(admission_fits([], candidate, candidate))
        self.assertFalse(admission_fits([], candidate, candidate - 1))

    def test_releasing_one_reservation_allows_next_solver(self):
        reservation = CAP + 2048
        active = [reservation, reservation]
        self.assertFalse(admission_fits(active, reservation, 201152))
        self.assertTrue(admission_fits(active[1:], reservation, 201152))
        self.assertEqual(active, [reservation, reservation])

    def test_active_request_limit_is_independent_of_available_tokens(self):
        reservation = CAP + 2048
        self.assertFalse(admission_fits([reservation] * 8, reservation, 10**9))
        self.assertTrue(admission_fits([reservation] * 7, reservation, 10**9))
        self.assertFalse(admission_fits([reservation] * 2, reservation, 10**9, max_active=2))
        self.assertFalse(admission_fits([], reservation, 10**9, max_active=0))

    def test_invalid_nonpositive_or_noninteger_reservations_are_rejected(self):
        for candidate in (0, -1, True, 81920.5, "81920"):
            with self.subTest(candidate=candidate):
                self.assertFalse(admission_fits([], candidate, 201152))
        for active in ([0], [-1], [True], [81920.5], ["81920"]):
            with self.subTest(active=active):
                self.assertFalse(admission_fits(active, CAP, 201152))
        for capacity in (0, -1, True, 201152.5, "201152"):
            with self.subTest(capacity=capacity):
                self.assertFalse(admission_fits([], CAP, capacity))


class CompletedReceiptTests(unittest.TestCase):
    def setUp(self):
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="resume_v7_test_", dir=TEMP_ROOT)
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / "synthetic_item_N"
        self.folder.mkdir()
        self.suffix = "\n[Synthetic unverified lookup.]\n"
        prefix = "Synthetic prefix: café e\u0301 and \\theta.\n"
        self.row = dict(
            family_id="synthetic_family",
            item_id="synthetic_item",
            prefix=prefix,
            prefix_sha256=hashlib.sha256(prefix.encode()).hexdigest(),
            seed=20261022,
            original_chat_prompt="Synthetic original prompt.\n<think>\n",
            original_image_pixels=[hashlib.sha256(b"synthetic pixels").hexdigest()],
            original_image_sizes=[[640, 480]],
            image="runs/stage14d1_pilot/synthetic_image_not_loaded.png",
        )
        self.input = dict(
            at="2026-10-22T00:00:00Z",
            id=self.folder.name,
            family_id=self.row["family_id"],
            item_id=self.row["item_id"],
            kind="solver",
            prompt=self.row["original_chat_prompt"] + prefix + self.suffix,
            pixels=deepcopy(self.row["original_image_pixels"]),
            sizes=deepcopy(self.row["original_image_sizes"]),
            images=[self.row["image"]],
            prefix_sha256=self.row["prefix_sha256"],
            sampling={"temperature": 0.7, "top_p": 0.8, "top_k": 20},
            cap=CAP,
            seed=self.row["seed"],
            job="synthetic_job",
            schema=None,
        )
        self.generation = dict(
            at="2026-10-22T00:00:01Z",
            id=self.folder.name,
            tokens=3,
            generated_token_ids=[11, 12, 13],
            raw_decoded_response="Synthetic fixture text, not a scientific answer.",
            prompt_token_ids=[21, 22, 23, 24],
            prompt_tokens=4,
            visual_tokens=0,
            finish_reason="stop",
            stop_reason=None,
            cap_hit=False,
            latency_seconds=1.0,
            job="synthetic_job",
            node="synthetic_node",
            seed=self.row["seed"],
        )
        self.commit()

    def commit(self):
        write_json(self.folder / "input.json", self.input)
        write_json(self.folder / "generation.json", self.generation)
        write_json(self.folder / "result.json", dict(
            input_sha256=digest(self.folder / "input.json"),
            generation_sha256=digest(self.folder / "generation.json"),
        ))

    def assert_rejected(self, row=None, suffix=None):
        with self.assertRaises(ValueError):
            completed_receipt(
                self.folder,
                self.row if row is None else row,
                self.suffix if suffix is None else suffix,
            )

    def test_valid_stop_receipt_returns_original_generation_path_without_mutation(self):
        before = {p.name: p.read_bytes() for p in self.folder.iterdir()}
        row_before = deepcopy(self.row)
        self.assertEqual(
            completed_receipt(self.folder, self.row, self.suffix),
            str(self.folder / "generation.json"),
        )
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.folder.iterdir()})
        self.assertEqual(self.row, row_before)

    def test_valid_length_completion_preserves_original_81920_cap(self):
        self.generation.update(
            tokens=CAP, generated_token_ids=[17] * CAP,
            finish_reason="length", cap_hit=True,
        )
        self.commit()
        self.assertEqual(
            completed_receipt(self.folder, self.row, self.suffix),
            str(self.folder / "generation.json"),
        )

    def test_missing_folder_and_uncommitted_interruption_return_none(self):
        self.assertIsNone(completed_receipt(self.folder / "missing", self.row, self.suffix))
        for name in ("result.json", "generation.json"):
            (self.folder / name).unlink()
        write_json(self.folder / "interrupted.json", dict(
            reason="ALLOCATION_DEADLINE", raw="synthetic partial", tokens=[11, 12],
        ))
        self.assertIsNone(completed_receipt(self.folder, self.row, self.suffix))

    def test_generation_without_commit_record_is_not_completed(self):
        (self.folder / "result.json").unlink()
        self.assertIsNone(completed_receipt(self.folder, self.row, self.suffix))

    def test_result_hash_mismatch_is_rejected_for_each_authenticated_file(self):
        for name in ("input.json", "generation.json"):
            with self.subTest(name=name):
                self.commit()
                with (self.folder / name).open("a", encoding="utf-8") as handle:
                    handle.write("\n")
                self.assert_rejected()

    def test_result_missing_hashes_bad_hashes_and_malformed_json_are_rejected(self):
        for record in (
            {}, [], None,
            {"input_sha256": "0" * 64, "generation_sha256": "0" * 64},
            {"input_sha256": digest(self.folder / "input.json")},
        ):
            with self.subTest(record=record):
                write_json(self.folder / "result.json", record)
                self.assert_rejected()
        (self.folder / "result.json").write_text("{broken", encoding="utf-8")
        self.assert_rejected()

    def test_committed_receipt_missing_input_or_generation_is_rejected(self):
        for name in ("input.json", "generation.json"):
            with self.subTest(name=name):
                self.commit()
                (self.folder / name).unlink()
                self.assert_rejected()

    def test_rehashed_input_identity_mismatches_are_rejected(self):
        original = deepcopy(self.input)
        changes = (
            {"family_id": "other_family"}, {"item_id": "other_item"},
            {"kind": "query"}, {"prefix_sha256": "0" * 64},
            {"seed": self.row["seed"] + 1}, {"cap": 256}, {"cap": CAP - 1},
            {"pixels": ["different_pixels"]}, {"sizes": [[480, 640]]},
            {"pixels": []}, {"sizes": []},
        )
        for change in changes:
            with self.subTest(change=change):
                self.input = dict(deepcopy(original), **change)
                self.commit()
                self.assert_rejected()

    def test_original_prompt_prefix_and_suffix_are_compared_exactly(self):
        original = self.input["prompt"]
        for prompt in (
            original + " ", original.replace("café", "cafe"),
            self.row["original_chat_prompt"] + self.suffix,
            self.row["original_chat_prompt"] + self.row["prefix"],
            original + "Synthetic interrupted continuation.",
        ):
            with self.subTest(prompt=prompt):
                self.input["prompt"] = prompt
                self.commit()
                self.assert_rejected()

    def test_requested_row_and_suffix_mismatches_are_rejected(self):
        for field, value in (
            ("family_id", "different_family"), ("item_id", "different_item"),
            ("seed", self.row["seed"] + 1),
            ("prefix", self.row["prefix"] + "changed"),
            ("prefix_sha256", "0" * 64),
            ("original_chat_prompt", "different prompt"),
            ("original_image_pixels", ["different_pixels"]),
            ("original_image_sizes", [[1, 1]]),
        ):
            with self.subTest(field=field):
                changed = dict(deepcopy(self.row), **{field: value})
                self.assert_rejected(row=changed)
        self.assert_rejected(suffix=self.suffix + "different")

    def test_rehashed_generation_seed_and_request_identity_mismatches_are_rejected(self):
        original = deepcopy(self.generation)
        for change in (
            {"seed": self.row["seed"] + 1}, {"id": "different_request"},
        ):
            with self.subTest(change=change):
                self.generation = dict(deepcopy(original), **change)
                self.commit()
                self.assert_rejected()

    def test_rehashed_noncompletion_or_inconsistent_termination_is_rejected(self):
        original = deepcopy(self.generation)
        for change in (
            {"finish_reason": None}, {"finish_reason": "abort"},
            {"finish_reason": "error"}, {"finish_reason": "length", "cap_hit": True},
            {"finish_reason": "stop", "cap_hit": True},
            {"tokens": 4}, {"tokens": -1}, {"tokens": CAP + 1},
        ):
            with self.subTest(change=change):
                self.generation = dict(deepcopy(original), **change)
                self.commit()
                self.assert_rejected()

    def test_authenticated_malformed_input_or_generation_is_rejected(self):
        for name in ("input.json", "generation.json"):
            with self.subTest(name=name):
                self.commit()
                (self.folder / name).write_text("{broken", encoding="utf-8")
                write_json(self.folder / "result.json", dict(
                    input_sha256=digest(self.folder / "input.json"),
                    generation_sha256=digest(self.folder / "generation.json"),
                ))
                self.assert_rejected()


if __name__ == "__main__":
    unittest.main()
