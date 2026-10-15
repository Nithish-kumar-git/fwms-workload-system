"""Run isolation regressions in a subprocess so adapters cannot leak to other tests."""
from pathlib import Path
import subprocess
import sys
import unittest


class DemoIsolationSuite(unittest.TestCase):
    def test_offline_demo_regressions(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable,'-B',str(root/'demo'/'verify_offline.py'),'-v'],
                                cwd=root, capture_output=True, text=True, timeout=120)
        if result.returncode:
            self.fail(result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
