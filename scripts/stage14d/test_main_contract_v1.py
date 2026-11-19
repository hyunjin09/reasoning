import unittest
from scripts.stage14d.main_contract_v1 import admit_scientific, release_main


class MainContractTest(unittest.TestCase):
    def release(self):
        return dict(user_approved=True,gpu_hours=375,cv_closed=False,cv_waiver_explicit=True,
                    calibration_pass=True,source_qc_sealed=True,anchors_sealed=True,
                    scientific_manifest_sealed=True,manifest_sha256='a',scientific_call_ceiling=1,concurrency=8)

    def test_numeric_budget_alone_does_not_waive_prerequisite(self):
        with self.assertRaises(ValueError):
            release_main(dict(self.release(),cv_waiver_explicit=False),'a',[dict(executable=True)])

    def test_different_manifest_and_extra_attempts_rejected(self):
        for change in [dict(manifest_sha256='b'),dict(scientific_call_ceiling=2),dict(concurrency=9)]:
            with self.assertRaises(ValueError):
                release_main(dict(self.release(),**change),'a',[dict(executable=True)])
        rows={'a':dict(executable=True),'b':dict(executable=False)}
        for tid,admitted in [('a',{'a'}),('b',set()),('c',set())]:
            with self.assertRaises(ValueError):
                admit_scientific(tid,rows,admitted,7200,3600)

    def test_insufficient_reserved_time_holds_before_call(self):
        with self.assertRaises(ValueError):
            admit_scientific('a',{'a':dict(executable=True)},set(),30,3600)

    def test_valid_release_and_attempt(self):
        release_main(self.release(),'a',[dict(executable=True)])
        admit_scientific('a',{'a':dict(executable=True)},set(),7200,3600)


if __name__=='__main__':unittest.main()
