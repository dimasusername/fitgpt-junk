# Database Schema

This directory contains the database schema for the AI Chat Application.

## Files

- `001_initial_schema.sql` - Complete database schema with pgvector extension
- `002_seed_data.sql` - Sample data for development and testing

## Database Schema

### Tables

1. **conversations** - Chat conversation metadata
2. **messages** - Individual chat messages with RAG sources and agent info
3. **documents** - Uploaded PDF documents with Supabase Storage integration
4. **document_chunks** - Text chunks with 768-dimensional vector embeddings

### Key Features

- **pgvector extension** for similarity search
- **HNSW vector indexing** for fast approximate nearest neighbor search
- **Row Level Security** policies enabled
- **Foreign key constraints** and performance indexes
- **Helper functions** for vector search and timestamp updates
- **Database views** for common queries

## Usage

1. Run `001_initial_schema.sql` in Supabase SQL Editor to create tables
2. Run `002_seed_data.sql` to add sample data
3. Test with `python test_db.py`

## Vector Search

The `search_document_chunks()` function provides semantic search:

```sql
SELECT * FROM search_document_chunks(
    query_embedding := your_768_dim_vector,
    similarity_threshold := 0.7,
    match_count := 10
);
```

## Testing

```bash
python test_db.py  # Test database connection and schema
```