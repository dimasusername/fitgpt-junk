# Vector Similarity Search Implementation

This document describes the enhanced vector similarity search functionality implemented for Task 6 of the AI Chat Application.

## Overview

The vector similarity search system provides advanced semantic search capabilities with:

- **Configurable similarity thresholds** for precision control
- **Advanced relevance scoring** with multiple ranking factors
- **Source attribution** with document and page information
- **Context-aware search** with surrounding chunks
- **Performance optimizations** using pgvector HNSW indexing

## Architecture

### Core Components

1. **VectorSearchService** (`app/services/vector_search.py`)
   - Main service class for vector similarity search
   - Handles query embedding generation
   - Implements advanced relevance scoring
   - Provides context-aware search capabilities

2. **Enhanced Database Functions** (`migrations/003_enhanced_vector_search.sql`)
   - Optimized pgvector similarity search functions
   - Multi-document filtering capabilities
   - Context chunk retrieval functions
   - Hybrid search combining vector and keyword matching

3. **Search API Endpoints** (`app/api/endpoints/search.py`)
   - RESTful API for vector search operations
   - Configurable search parameters
   - Statistics and analytics endpoints

## Features Implemented

### 1. Configurable Similarity Thresholds

```python
config = SearchConfig(
    similarity_threshold=0.7,  # Minimum similarity score (0-1)
    max_results=10,           # Maximum number of results
    boost_recent_docs=True,   # Boost recently uploaded documents
    boost_page_context=True,  # Boost based on page position
    include_metadata=True     # Include chunk metadata
)
```

### 2. Advanced Relevance Scoring

The system calculates enhanced relevance scores based on:

- **Base similarity score** from vector cosine similarity
- **Keyword matching boost** for exact term matches
- **Recency boost** for recently uploaded documents
- **Page context boost** for chunks from early pages
- **Content length normalization** for substantial chunks

### 3. Source Attribution

Each search result includes detailed source information:

```python
source_attribution = "Roman Army Structure.pdf, p. 15 (military_structure)"
```

Format: `{document_name}, p. {page_number} ({topic})`

### 4. Context-Aware Search

Retrieve surrounding chunks for better context:

```python
results = await search_service.search_with_context(
    query="Roman military tactics",
    context_window=1  # Include 1 chunk before/after
)
```

### 5. Document Filtering

Search within specific documents or document sets:

```python
# Single document
results = await search_service.search(
    query="legion structure",
    document_id="doc-uuid"
)

# Multiple documents
results = await search_service.search(
    query="military tactics",
    document_ids=["doc-1", "doc-2"]
)
```

## API Endpoints

### POST /api/search
Main vector similarity search endpoint.

**Request:**
```json
{
  "query": "Roman legion structure",
  "similarity_threshold": 0.7,
  "max_results": 10,
  "document_id": "optional-doc-id",
  "boost_recent_docs": true,
  "boost_page_context": true,
  "include_metadata": true
}
```

**Response:**
```json
{
  "query": "Roman legion structure",
  "results": [
    {
      "chunk_id": "chunk-uuid",
      "document_id": "doc-uuid",
      "content": "Roman legions were highly organized...",
      "similarity_score": 0.85,
      "relevance_score": 0.87,
      "page_number": 15,
      "source_attribution": "Roman Army.pdf, p. 15",
      "metadata": {"topic": "military_structure"}
    }
  ],
  "total_results": 1,
  "execution_time_ms": 45.2
}
```

### POST /api/search/context
Context-aware search with surrounding chunks.

### GET /api/search/stats
Search index statistics and analytics.

### GET /api/search/test
Simple test endpoint for quick searches.

### POST /api/search/rerank
Rerank search results with custom boost factors.

## Database Schema

### Enhanced Search Functions

1. **search_document_chunks()** - Core vector similarity search
2. **search_document_chunks_multi()** - Multi-document filtering
3. **get_context_chunks()** - Context chunk retrieval
4. **hybrid_search_chunks()** - Vector + keyword hybrid search
5. **get_search_statistics()** - Index statistics

### Optimized Indexes

- **HNSW vector index** for fast approximate nearest neighbor search
- **GIN text index** for keyword search capabilities
- **Composite indexes** for filtered searches

## Performance Optimizations

### Vector Search Optimizations

1. **HNSW Algorithm**: Fast approximate nearest neighbor search
2. **Configurable Parameters**: 
   - `m = 16` (connections per node)
   - `ef_construction = 64` (search width during construction)
3. **Batch Processing**: Efficient embedding generation
4. **Connection Pooling**: Optimized database connections

### Query Optimizations

1. **Similarity Threshold Filtering**: Early result filtering
2. **Result Limiting**: Configurable result set sizes
3. **Index Hints**: Optimized query execution plans
4. **Materialized Views**: Pre-computed analytics

## Usage Examples

### Basic Search

```python
from app.services.vector_search import vector_search_service, SearchConfig

config = SearchConfig(similarity_threshold=0.7, max_results=5)
results = await vector_search_service.search("Roman military tactics", config)

for result in results:
    print(f"Score: {result.relevance_score:.3f}")
    print(f"Source: {result.source_attribution}")
    print(f"Content: {result.content[:100]}...")
```

### Context Search

```python
context_results = await vector_search_service.search_with_context(
    query="Greek phalanx formation",
    context_window=2
)

for result in context_results:
    print(f"Primary: {result['primary_chunk']['content']}")
    print(f"Context: {len(result['context_chunks'])} surrounding chunks")
```

### Filtered Search

```python
# Search within specific document
results = await vector_search_service.search(
    query="centurion leadership",
    config=config,
    document_id="roman-army-doc-id"
)
```

## Testing

### Unit Tests
- `tests/unit/test_vector_search.py` - Core functionality tests
- Coverage for all search configurations and edge cases

### Integration Tests
- `tests/integration/test_search_api.py` - API endpoint tests
- End-to-end search workflow validation

### Demo Script
- `demo_vector_search.py` - Interactive demonstration
- Shows all search capabilities with sample data

## Configuration

### Environment Variables

```bash
# Required for vector search
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key

# Optional search configuration
EMBEDDING_MODEL=text-embedding-004
MAX_SEARCH_RESULTS=50
DEFAULT_SIMILARITY_THRESHOLD=0.7
```

### Search Configuration

```python
class SearchConfig:
    similarity_threshold: float = 0.7    # Minimum similarity (0-1)
    max_results: int = 10               # Maximum results
    boost_recent_docs: bool = True      # Boost recent documents
    boost_page_context: bool = True     # Boost early pages
    min_content_length: int = 50        # Minimum chunk length
    include_metadata: bool = True       # Include metadata
```

## Monitoring and Analytics

### Search Statistics

The system provides comprehensive search analytics:

- Total searchable chunks
- Ready documents count
- Average chunk length
- Embedding coverage percentage
- Search performance metrics

### Performance Monitoring

- Query execution times
- Result relevance scores
- Search result distributions
- Error rates and patterns

## Requirements Satisfied

This implementation satisfies all requirements from Task 6:

✅ **Implement pgvector similarity search with configurable similarity thresholds**
- Configurable `similarity_threshold` parameter
- HNSW-optimized pgvector search functions

✅ **Create query embedding generation and vector search optimization**
- Google Gemini embedding generation for queries
- Optimized database functions and indexes
- Batch processing and connection pooling

✅ **Build result ranking and relevance scoring with source attribution**
- Multi-factor relevance scoring algorithm
- Keyword matching, recency, and context boosts
- Detailed source attribution with document and page info

✅ **Add search result formatting with document sources and page numbers**
- Structured search result objects
- Formatted source attribution strings
- Rich metadata inclusion

The implementation provides a production-ready vector similarity search system with advanced features for semantic document search and retrieval.