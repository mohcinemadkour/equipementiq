"""
Fine-grained latency profiling for support agent retrieval.
Breaks down: embedding → query → reranking operations.
"""

import time
from agents.support_agent import SupportAgent

def profile_support_retrieval():
    query = "Show me complaint case CMP-2019-1000"
    agent = SupportAgent()
    
    print(f"Query: {query!r}")
    print("=" * 80)
    print("DETAILED SUPPORT AGENT PROFILING")
    print("=" * 80)
    print()
    
    # Step 1: Embedding
    print("Step 1: Query Embedding (OpenAI API)")
    print("-" * 80)
    start_embed = time.time()
    query_embedding = agent._embedder.embed_query(query)
    embed_time = time.time() - start_embed
    print(f"  Time: {embed_time:.3f}s")
    print(f"  Embedding dims: {len(query_embedding)}")
    print()
    
    # Step 2: ChromaDB Query
    print("Step 2: ChromaDB Query (Semantic Search)")
    print("-" * 80)
    top_k = agent._config["retrieval"]["top_k_retrieval"]
    start_query = time.time()
    results = agent._collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=None,
        include=["documents", "metadatas", "distances", "embeddings"],
    )
    query_time = time.time() - start_query
    
    retrieved_count = len(results["ids"][0]) if results["ids"] else 0
    print(f"  Time: {query_time:.3f}s")
    print(f"  Retrieved: {retrieved_count} documents (top_k={top_k})")
    print()
    
    # Step 3: Distance Conversion
    print("Step 3: Distance → Similarity Conversion & Filtering")
    print("-" * 80)
    start_filter = time.time()
    retrieval_results = []
    oos_floor = agent._config["retrieval"]["oos_similarity_floor"]
    
    for doc_id, doc, metadata, distance in zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        similarity = 1 - (distance ** 2 / 2)
        if similarity < oos_floor:
            continue
        retrieval_results.append(
            {
                "chunk_id": metadata.get("chunk_id", "unknown"),
                "source_document": metadata.get("source_document", "unknown"),
                "content": doc,
                "similarity_score": similarity,
                "metadata": metadata,
            }
        )
    
    filter_time = time.time() - start_filter
    print(f"  Time: {filter_time:.3f}s")
    print(f"  After filtering: {len(retrieval_results)} documents")
    print(f"  OOS floor: {oos_floor}")
    print()
    
    # Step 4: Reranking
    print("Step 4: CrossEncoder Reranking")
    print("-" * 80)
    start_rerank = time.time()
    
    # Build pairs for reranking
    pairs = [(query, r["content"]) for r in retrieval_results]
    rerank_scores = agent._reranker.predict(pairs)
    
    rerank_time = time.time() - start_rerank
    print(f"  Time: {rerank_time:.3f}s")
    print(f"  Documents reranked: {len(pairs)}")
    if pairs:
        print(f"  Avg score: {sum(rerank_scores) / len(rerank_scores):.3f}")
    print()
    
    # Summary
    print("=" * 80)
    print("TIMING SUMMARY")
    print("=" * 80)
    total_time = embed_time + query_time + filter_time + rerank_time
    print(f"Query Embedding:  {embed_time:7.3f}s ({embed_time/total_time*100:5.1f}%)")
    print(f"ChromaDB Query:   {query_time:7.3f}s ({query_time/total_time*100:5.1f}%)")
    print(f"Filtering:        {filter_time:7.3f}s ({filter_time/total_time*100:5.1f}%)")
    print(f"Reranking:        {rerank_time:7.3f}s ({rerank_time/total_time*100:5.1f}%)")
    print("-" * 80)
    print(f"TOTAL:            {total_time:7.3f}s (100.0%)")
    print()
    
    # Identify bottleneck
    times = [
        ("Query Embedding", embed_time),
        ("ChromaDB Query", query_time),
        ("Filtering", filter_time),
        ("Reranking", rerank_time),
    ]
    times_sorted = sorted(times, key=lambda x: x[1], reverse=True)
    
    worst_name, worst_time = times_sorted[0]
    worst_pct = worst_time / total_time * 100
    
    print("=" * 80)
    print(f"⚠️  BOTTLENECK: {worst_name}")
    print(f"    Consuming {worst_time:.3f}s ({worst_pct:.1f}% of retrieval)")
    print("=" * 80)
    print()
    
    # Recommendations
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if worst_name == "Reranking":
        print("❌ CrossEncoder reranking is the bottleneck")
        print("   SOLUTIONS:")
        print("   1. Cache the CrossEncoder model (first load is slow)")
        print("   2. Reduce top_k_retrieval (fewer docs to rerank)")
        print("   3. Skip reranking for simple queries (add config flag)")
        print("   4. Use a smaller/faster reranker model")
        print("   5. Pre-filter low-quality results before reranking")
    elif worst_name == "Query Embedding":
        print("❌ OpenAI API embedding generation is the bottleneck")
        print("   SOLUTIONS:")
        print("   1. Cache embeddings in-memory or Redis")
        print("   2. Use OpenAI Batch API for off-peak generation")
        print("   3. Switch to open-source embedder (e.g., bge-small-en)")
        print("   4. Pre-compute common query embeddings")
    elif worst_name == "ChromaDB Query":
        print("❌ ChromaDB vector search is slow")
        print("   SOLUTIONS:")
        print("   1. Rebuild collection with optimized settings")
        print("   2. Check ChromaDB indexing (try re-indexing)")
        print("   3. Monitor disk I/O (may be I/O bound)")
        print("   4. Consider switching to Pinecone/Weaviate")
    else:
        print("✅ All operations are reasonably fast")

if __name__ == "__main__":
    profile_support_retrieval()
