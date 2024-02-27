from bx_py_utils.test_utils.unittest_utils import BaseDocTests, DocTestResults

import huey_monitor
import huey_monitor_project


class DocTests(BaseDocTests):
    def test_doctests(self):
        results: DocTestResults = self.run_doctests(
            modules=(
                huey_monitor,
                huey_monitor_project,
            )
        )
        self.assertGreaterEqual(results.passed, 25)
        self.assertEqual(results.skipped, 0)
        self.assertLessEqual(results.failed, 0)
