#!/usr/bin/env python3
"""Ingest all collections for pre-merge checklist"""

print("=" * 70)
print("Ingesting all collections...")
print("=" * 70)

try:
    print("\n1️⃣  Ingesting mechanical PDFs...")
    from ingestion.ingest_mechanical import run as run_mechanical
    run_mechanical()
    print("✅ Mechanical collection populated")
except Exception as e:
    print(f"❌ Mechanical ingestion failed: {e}")
    raise

try:
    print("\n2️⃣  Ingesting software error codes...")
    from ingestion.ingest_software import run as run_software
    run_software()
    print("✅ Software collection populated")
except Exception as e:
    print(f"❌ Software ingestion failed: {e}")
    raise

try:
    print("\n3️⃣  Ingesting support complaints...")
    from ingestion.ingest_support import run as run_support
    run_support()
    print("✅ Support collection populated")
except Exception as e:
    print(f"❌ Support ingestion failed: {e}")
    raise

print("\n" + "=" * 70)
print("✅ All collections ingested successfully!")
print("=" * 70)
