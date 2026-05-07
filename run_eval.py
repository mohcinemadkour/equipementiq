"""Wrapper to run batch evaluation with proper output."""

import sys
import subprocess

result = subprocess.run(
    [sys.executable, "evaluation/batch_eval.py"],
    env={"PYTHONPATH": "."},
    capture_output=False,
    text=True
)

sys.exit(result.returncode)
