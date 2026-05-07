#!/usr/bin/env python3
"""Check ChromaDB collection sizes"""

import chromadb

print("ChromaDB Collection Status:")
print("=" * 50)

c = chromadb.PersistentClient('./chroma_db')
for col in c.list_collections():
    count = col.count()
    print(f"  {col.name}: {count} chunks", end="")
    if count == 0:
        print(" ⚠️  WARNING: Collection is empty!")
    else:
        print(" ✅")

print("=" * 50)
