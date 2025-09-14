#!/usr/bin/env python3
"""
Demonstration script for vector similarity search functionality.

This script shows how to use the enhanced vector search service with:
- Configurable similarity thresholds
- Advanced relevance scoring and ranking
- Source attribution with document and page information
- Context-aware search with surrounding chunks
"""
import asyncio
import logging
from typing import List

from app.services.vector_search import VectorSearchService, SearchConfig
from app.core.database import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_basic_search():
    """Demonstrate basic vector similarity search."""
    print("\n=== Basic Vector Search Demo ===")
    
    search_service = VectorSearchService()
    
    # Configure search parameters
    config = SearchConfig(
        similarity_threshold=0.7,
        max_results=5,
        boost_recent_docs=True,
        boost_page_context=True,
        include_metadata=True
    )
    
    # Example search queries
    queries = [
        "Roman legion military structure",
        "Greek phalanx formation tactics",
        "Ancient warfare strategies",
        "Centurion leadership hierarchy"
    ]
    
    for query in queries:
        print(f"\nSearching for: '{query}'")
        try:
            results = await search_service.search(query, config)
            
            if results:
                print(f"Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. Similarity: {result.similarity_score:.3f}, "
                          f"Relevance: {result.relevance_score:.3f}")
                    print(f"     Source: {result.source_attribution}")
                    print(f"     Content: {result.content[:100]}...")
                    if result.metadata:
                        print(f"     Metadata: {result.metadata}")
            else:
                print("  No results found")
                
        except Exception as e:
            print(f"  Search failed: {e}")


async def demo_context_search():
    """Demonstrate context-aware search with surrounding chunks."""
    print("\n=== Context-Aware Search Demo ===")
    
    search_service = VectorSearchService()
    
    query = "Roman military tactics evolution"
    context_window = 1
    
    print(f"Searching with context for: '{query}'")
    print(f"Context window: {context_window} chunks before/after")
    
    try:
        results = await search_service.search_with_context(
            query=query,
            context_window=context_window
        )
        
        if results:
            print(f"Found {len(results)} results with context:")
            for i, result in enumerate(results, 1):
                print(f"\n  Result {i}:")
                print(f"    Primary chunk: {result['primary_chunk']['source_attribution']}")
                print(f"    Similarity: {result['primary_chunk']['similarity_score']:.3f}")
                print(f"    Context chunks: {len(result['context_chunks'])}")
                print(f"    Full context preview: {result['full_context'][:200]}...")
        else:
            print("  No results found")
            
    except Exception as e:
        print(f"  Context search failed: {e}")


async def demo_filtered_search():
    """Demonstrate search with document filtering."""
    print("\n=== Filtered Search Demo ===")
    
    search_service = VectorSearchService()
    
    query = "military organization"
    
    # Search within specific document
    print(f"Searching within specific document for: '{query}'")
    try:
        config = SearchConfig(similarity_threshold=0.6, max_results=3)
        results = await search_service.search(
            query=query,
            config=config,
            document_id="770e8400-e29b-41d4-a716-446655440001"  # Roman army document
        )
        
        if results:
            print(f"Found {len(results)} results in specific document:")
            for result in results:
                print(f"  - {result.source_attribution}")
                print(f"    Relevance: {result.relevance_score:.3f}")
        else:
            print("  No results found in specific document")
            
    except Exception as e:
        print(f"  Filtered search failed: {e}")
    
    # Search across multiple documents
    print(f"\nSearching across multiple documents for: '{query}'")
    try:
        results = await search_service.search(
            query=query,
            config=config,
            document_ids=[
                "770e8400-e29b-41d4-a716-446655440001",  # Roman army
                "770e8400-e29b-41d4-a716-446655440003"   # Greek warfare
            ]
        )
        
        if results:
            print(f"Found {len(results)} results across multiple documents:")
            for result in results:
                print(f"  - {result.source_attribution}")
                print(f"    Relevance: {result.relevance_score:.3f}")
        else:
            print("  No results found across multiple documents")
            
    except Exception as e:
        print(f"  Multi-document search failed: {e}")


async def demo_search_configuration():
    """Demonstrate different search configurations."""
    print("\n=== Search Configuration Demo ===")
    
    search_service = VectorSearchService()
    query = "Roman legion"
    
    # High precision search
    print("High precision search (threshold=0.8):")
    try:
        config = SearchConfig(
            similarity_threshold=0.8,
            max_results=3,
            boost_recent_docs=False,
            boost_page_context=False
        )
        results = await search_service.search(query, config)
        print(f"  Found {len(results)} high-precision results")
        
    except Exception as e:
        print(f"  High precision search failed: {e}")
    
    # Broad search with boosting
    print("\nBroad search with boosting (threshold=0.6):")
    try:
        config = SearchConfig(
            similarity_threshold=0.6,
            max_results=10,
            boost_recent_docs=True,
            boost_page_context=True
        )
        results = await search_service.search(query, config)
        print(f"  Found {len(results)} broad results with boosting")
        
    except Exception as e:
        print(f"  Broad search failed: {e}")


async def demo_search_statistics():
    """Demonstrate search statistics and analytics."""
    print("\n=== Search Statistics Demo ===")
    
    search_service = VectorSearchService()
    
    try:
        stats = await search_service.get_search_statistics()
        
        print("Search Index Statistics:")
        print(f"  Total searchable chunks: {stats['total_searchable_chunks']}")
        print(f"  Ready documents: {stats['ready_documents']}")
        print(f"  Average chunk length: {stats['average_chunk_length']} characters")
        print(f"  Embedding dimension: {stats['embedding_dimension']}")
        print(f"  Search algorithm: {stats['search_algorithm']}")
        print(f"  Similarity metric: {stats['similarity_metric']}")
        
    except Exception as e:
        print(f"  Statistics retrieval failed: {e}")


async def main():
    """Run all vector search demonstrations."""
    print("Vector Similarity Search Functionality Demo")
    print("=" * 50)
    
    try:
        # Initialize database connection
        await init_db()
        print("Database initialized successfully")
        
        # Run demonstrations
        await demo_basic_search()
        await demo_context_search()
        await demo_filtered_search()
        await demo_search_configuration()
        await demo_search_statistics()
        
        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        
    except Exception as e:
        print(f"Demo failed: {e}")
        print("\nNote: This demo requires a properly configured database with:")
        print("- Supabase connection")
        print("- pgvector extension enabled")
        print("- Sample documents with embeddings")
        print("- Google Gemini API key for embedding generation")


if __name__ == "__main__":
    asyncio.run(main())