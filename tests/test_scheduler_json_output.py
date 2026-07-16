import json
import subprocess
import sys
import unittest
from pathlib import Path


class SchedulerJsonOutputTests(unittest.TestCase):
    def test_main_json_emits_valid_json(self):
        project_root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "work/scripts/main.py", "--json"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("candidates", payload)
        self.assertGreaterEqual(len(payload["candidates"]), 1)


if __name__ == "__main__":
    unittest.main()
