#!/usr/bin/env python3
"""Diagnose why chunks are retrieved but then filtered during synthesis."""

from dotenv import load_dotenv
load_dotenv()

import chromadb
import os
from ingestion.config import load_config
from langchain_openai import OpenAIEmbeddings

cfg = load_config()
embedder = OpenAIEmbeddings(model=cfg['embeddings']['model'])
client = chromadb.PersistentClient(path=os.getenv('CHROMA_PERSIST_DIR', './chroma_db'))
soft_col = client.get_collection('software_collection')

queries = [
    'What action does a WARNING severity error require?',
    'Which error codes are related to SPN-MJ-002?',
    'What does error CLS-CR-001 mean and when is it triggered?',
    'What does error ELC-CR-001 indicate?',
    'What is the probable cause of error SPN-MJ-004?',
    'How many severity levels does the error code system have?',
    'What error code fires when the ATC arm collides?',
    'What does a NOTICE severity error require the operator to do?',
    'What is the required action for error code THM-CR-001?',
]

print("=" * 100)
print("DIAGNOSING CHUNK RETRIEVAL & SIMILARITY SCORES")
print(f"OOS Similarity Floor: {cfg['retrieval'].get('oos_similarity_floor', 0.15)}")
print("=" * 100)

for q in queries:
    print(f'\nQuery: {q}')
    
    # Retrieve from ChromaDB
    results = soft_col.query(query_texts=[q], n_results=5, include=['distances', 'metadatas'])
    
    if results['ids'] and results['ids'][0]:
        print(f'  Retrieved {len(results["ids"][0])} chunks:')
        for chunk_id, distance, metadata in zip(results['ids'][0], results['distances'][0], results['metadatas'][0]):
            # Convert distance to similarity score
            similarity = 1 - (distance ** 2 / 2)
            source_doc = metadata.get('source_document', 'unknown')
            print(f'    [{similarity:.4f}] {chunk_id[:30]:30} (source: {source_doc})')
    else:
        print(f'  NO CHUNKS RETRIEVED')

print("\n" + "=" * 100)
