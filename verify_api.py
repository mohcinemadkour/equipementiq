#!/usr/bin/env python3
"""API verification script for EquipmentIQ"""

import os, sys
from pathlib import Path

# Force reload of .env
from dotenv import load_dotenv
dotenv_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path, override=True)

print('=== Key Check ===')
keys_ok = True
for k in ['ANTHROPIC_API_KEY','OPENAI_API_KEY','LANGCHAIN_API_KEY','LANGCHAIN_PROJECT']:
    v = os.getenv(k,'')
    if v:
        print(f'  {k}: OK — {v[:15]}...')
    else:
        print(f'  {k}: MISSING')
        keys_ok = False

if not keys_ok:
    print('\n⚠️  Some keys missing — cannot continue')
    sys.exit(1)

print('\n=== API Test ===')

try:
    import anthropic
    c = anthropic.Anthropic()
    r = c.messages.create(model='claude-haiku-4-5-20251001',
        max_tokens=10, messages=[{'role':'user','content':'ping'}])
    print('  Anthropic: OK')
except Exception as e:
    print(f'  Anthropic: FAILED — {e}')
    sys.exit(1)

try:
    import openai
    e = openai.OpenAI().embeddings.create(
        model='text-embedding-3-small', input='test')
    print(f'  OpenAI embeddings: OK (dims={len(e.data[0].embedding)})')
except Exception as e:
    print(f'  OpenAI embeddings: FAILED — {e}')
    sys.exit(1)

print('\n✅ All systems GO — ready for ingestion')
