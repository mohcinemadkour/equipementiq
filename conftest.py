"""Pytest configuration - load .env before importing tests"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env at the very beginning
dotenv_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path, override=True)

# Verify API key is available
api_key = os.getenv('ANTHROPIC_API_KEY', '').strip()
if api_key and 'REPLACE' not in api_key.upper():
    print(f"\n[OK] pytest: ANTHROPIC_API_KEY loaded ({api_key[:20]}...)\n")
else:
    print("\n[WARN] pytest: ANTHROPIC_API_KEY not available or placeholder\n")
