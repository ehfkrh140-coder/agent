import subprocess
import sys
import unittest


class AuthWarmupImportTests(unittest.TestCase):
    def test_auth_warmup_help_runs(self):
        completed = subprocess.run([sys.executable, "tools/auth_warmup.py", "--help"], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0)


if __name__ == "__main__":
    unittest.main()
