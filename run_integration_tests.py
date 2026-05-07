#!/usr/bin/env python3
"""Run integration tests with proper API key loading"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env first
dotenv_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path, override=True)

# Verify the key is loaded and valid
api_key = os.getenv('ANTHROPIC_API_KEY', '').strip()
if not api_key or 'REPLACE' in api_key.upper():
    print("❌ ANTHROPIC_API_KEY not valid")
    sys.exit(1)

print(f"✅ API Key loaded: {api_key[:30]}...")

# Now run the tests
import subprocess
result = subprocess.run([
    sys.executable, '-m', 'pytest',
    'tests/test_orchestrator.py::TestOrchestratorIntegration',
    '-v', '--tb=short'
], cwd=str(Path(__file__).parent))

sys.exit(result.returncode)
