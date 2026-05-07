"""Check actual source_document values in ChromaDB collections."""

import chromadb

client = chromadb.PersistentClient(path='./chroma_db')

# Check what source_document values are actually in the collections
for cname in ['software_collection', 'mechanical_collection', 'support_collection']:
    print(f"\n{'='*60}")
    print(f"{cname}")
    print(f"{'='*60}")
    
    coll = client.get_collection(name=cname)
    results = coll.get(limit=20)
    
    if results['metadatas']:
        seen = set()
        for m in results['metadatas']:
            src = m.get('source_document', 'N/A')
            if src not in seen:
                print(f"  {src}")
                seen.add(src)
