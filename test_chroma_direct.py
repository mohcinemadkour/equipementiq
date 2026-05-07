"""Test ChromaDB directly."""

import chromadb
from langchain_openai import OpenAIEmbeddings

client = chromadb.PersistentClient(path='./chroma_db')
coll = client.get_collection(name='software_collection')

embedder = OpenAIEmbeddings(model='text-embedding-3-small')
query = "What is SPN-CR-001?"
query_embedding = embedder.embed_query(query)

# Query ChromaDB
results = coll.query(
    query_embeddings=[query_embedding],
    n_results=5,
    include=["documents", "metadatas", "distances"],
)

print(f"Query: {query}")
print(f"Num results from ChromaDB: {len(results['ids'][0])}")

for i, (doc_id, doc, meta, dist) in enumerate(zip(
    results['ids'][0],
    results['documents'][0],
    results['metadatas'][0],
    results['distances'][0],
)):
    print(f"\n{i+1}. {meta.get('source_document', 'N/A')}")
    print(f"   distance={dist:.4f}")
    print(f"   doc_id={doc_id}")
