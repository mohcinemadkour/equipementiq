"""Check actual similarity scores."""

import chromadb
from openai import OpenAI

client = chromadb.PersistentClient(path='./chroma_db')
coll = client.get_collection(name='software_collection')

# Get OpenAI embedder
from langchain_openai import OpenAIEmbeddings
embedder = OpenAIEmbeddings(model='text-embedding-3-small')

# Query
query = "What is SPN-CR-001?"
query_embedding = embedder.embed_query(query)

print(f"Query: {query}")
print(f"Query embedding shape: {len(query_embedding)}")

# Query ChromaDB
results = coll.query(
    query_embeddings=[query_embedding],
    n_results=10,
    include=["documents", "metadatas", "distances"],
)

print(f"\nTop 10 results:")
for doc_id, doc, metadata, distance in zip(
    results["ids"][0],
    results["documents"][0],
    results["metadatas"][0],
    results["distances"][0],
):
    # Try different similarity conversions
    sim_1 = 1 - (distance / 2)  # Current formula
    sim_2 = 1 - distance         # Alternative
    
    src = metadata.get('source_document', 'N/A')
    print(f"\n{src}")
    print(f"  distance={distance:.4f}, sim_1-distance/2={sim_1:.4f}, sim_2=1-distance={sim_2:.4f}")
