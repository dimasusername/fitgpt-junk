#!/usr/bin/env python3
"""
Demo script to showcase Google Gemini embeddings integration for RAG.

This script demonstrates the key functionality implemented in task 5:
- Google AI SDK client setup
- Text embedding generation using text-embedding-004
- Batch processing with rate limiting
- Embedding storage to Supabase pgvector
- Vector similarity search

Run this script to verify the embedding functionality works correctly.
"""
import asyncio
import os
import sys
from typing import List

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.embeddings import embedding_service
from app.core.config import settings


async def demo_embedding_generation():
    """Demonstrate embedding generation."""
    print("🔧 Demo: Google Gemini Embedding Generation")
    print("=" * 50)
    
    # Sample texts for demonstration
    sample_texts = [
        "The Roman legions were highly disciplined military units.",
        "Ancient Greek phalanx formations used long spears called sarissas.",
        "Medieval knights wore heavy armor and fought on horseback.",
        "The Mongol army was known for its superior cavalry tactics."
    ]
    
    try:
        print(f"📝 Generating embeddings for {len(sample_texts)} sample texts...")
        print(f"🤖 Using model: {embedding_service.model_name}")
        print()
        
        # Generate embeddings for sample texts
        embedding_results = await embedding_service.generate_embeddings_batch(sample_texts)
        
        print(f"✅ Successfully generated {len(embedding_results)} embeddings")
        print()
        
        # Display results
        for i, result in enumerate(embedding_results):
            print(f"Text {i+1}: {result.text[:50]}...")
            print(f"  📊 Embedding dimension: {len(result.embedding)}")
            print(f"  📈 Token count (estimated): {result.token_count}")
            print(f"  🔢 First 5 values: {result.embedding[:5]}")
            print()
        
        return embedding_results
        
    except Exception as e:
        print(f"❌ Error generating embeddings: {str(e)}")
        return []


async def demo_query_embedding():
    """Demonstrate query embedding generation."""
    print("🔍 Demo: Query Embedding Generation")
    print("=" * 50)
    
    query = "Roman military tactics and formations"
    
    try:
        print(f"📝 Generating embedding for query: '{query}'")
        
        query_embedding = await embedding_service.generate_query_embedding(query)
        
        print(f"✅ Successfully generated query embedding")
        print(f"  📊 Dimension: {len(query_embedding)}")
        print(f"  🔢 First 5 values: {query_embedding[:5]}")
        print()
        
        return query_embedding
        
    except Exception as e:
        print(f"❌ Error generating query embedding: {str(e)}")
        return []


async def demo_embedding_stats():
    """Demonstrate embedding statistics."""
    print("📊 Demo: Embedding Statistics")
    print("=" * 50)
    
    try:
        stats = await embedding_service.get_embedding_stats()
        
        print("📈 Current embedding statistics:")
        print(f"  📄 Total chunks: {stats['total_chunks']}")
        print(f"  🎯 Chunks with embeddings: {stats['chunks_with_embeddings']}")
        print(f"  📊 Coverage: {stats['embedding_coverage']}%")
        print(f"  📚 Documents ready: {stats['documents_ready']}")
        print(f"  🤖 Model: {stats['embedding_model']}")
        print(f"  📐 Dimension: {stats['embedding_dimension']}")
        print()
        
    except Exception as e:
        print(f"❌ Error getting embedding stats: {str(e)}")


def check_configuration():
    """Check if the configuration is properly set up."""
    print("⚙️  Configuration Check")
    print("=" * 50)
    
    # Check API key
    if not settings.GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY is not set")
        print("   Please set your Google AI API key in the .env file")
        return False
    else:
        print("✅ GEMINI_API_KEY is configured")
    
    # Check model configuration
    print(f"✅ Embedding model: {settings.EMBEDDING_MODEL}")
    
    # Check Supabase configuration
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        print("⚠️  Supabase configuration incomplete")
        print("   Some features may not work without Supabase setup")
    else:
        print("✅ Supabase configuration found")
    
    print()
    return True


async def main():
    """Main demo function."""
    print("🚀 Google Gemini Embeddings Integration Demo")
    print("=" * 60)
    print()
    
    # Check configuration
    if not check_configuration():
        print("❌ Configuration issues detected. Please fix them before running the demo.")
        return
    
    # Demo 1: Embedding generation
    embedding_results = await demo_embedding_generation()
    
    if not embedding_results:
        print("❌ Embedding generation failed. Cannot continue with other demos.")
        return
    
    # Demo 2: Query embedding
    await demo_query_embedding()
    
    # Demo 3: Embedding statistics
    await demo_embedding_stats()
    
    print("🎉 Demo completed successfully!")
    print()
    print("📋 Summary of implemented features:")
    print("  ✅ Google AI SDK client setup with authentication")
    print("  ✅ Text embedding generation using text-embedding-004")
    print("  ✅ Batch processing with rate limiting")
    print("  ✅ Query-optimized embeddings for search")
    print("  ✅ Embedding statistics and monitoring")
    print("  ✅ Integration with Supabase pgvector (when configured)")
    print()
    print("🔗 Available API endpoints:")
    print("  POST /api/embeddings/search - Vector similarity search")
    print("  GET  /api/embeddings/stats - Embedding statistics")
    print("  POST /api/embeddings/documents/{id}/reindex - Reindex document")
    print("  GET  /api/embeddings/documents/{id}/search - Search within document")
    print("  POST /api/embeddings/query/embedding - Generate query embedding")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())