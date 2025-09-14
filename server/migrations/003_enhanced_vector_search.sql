-- Enhanced vector search functions and optimizations
-- This migration adds improved vector search capabilities with better performance and ranking

-- Drop existing function to replace with enhanced version
DROP FUNCTION IF EXISTS search_document_chunks(vector(768), float, int);

-- Enhanced vector similarity search function with better performance
CREATE OR REPLACE FUNCTION search_document_chunks(
    query_embedding vector(768),
    similarity_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10,
    document_filter uuid DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    content text,
    page_number integer,
    chunk_index integer,
    similarity float,
    document_filename text,
    document_original_name text,
    document_uploaded_at timestamp with time zone,
    chunk_length integer,
    metadata jsonb
)
LANGUAGE sql
STABLE
AS $function$
    SELECT 
        dc.id,
        dc.document_id,
        dc.content,
        dc.page_number,
        dc.chunk_index,
        1 - (dc.embedding <=> query_embedding) as similarity,
        d.filename,
        d.original_name,
        d.uploaded_at,
        LENGTH(dc.content) as chunk_length,
        dc.metadata
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE d.status = 'ready'
    AND dc.embedding IS NOT NULL
    AND 1 - (dc.embedding <=> query_embedding) > similarity_threshold
    AND (document_filter IS NULL OR dc.document_id = document_filter)
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
$function$;

-- Function for searching within multiple specific documents
CREATE OR REPLACE FUNCTION search_document_chunks_multi(
    query_embedding vector(768),
    document_ids uuid[],
    similarity_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    content text,
    page_number integer,
    chunk_index integer,
    similarity float,
    document_filename text,
    document_original_name text,
    document_uploaded_at timestamp with time zone,
    chunk_length integer,
    metadata jsonb
)
LANGUAGE sql
STABLE
AS $function$
    SELECT 
        dc.id,
        dc.document_id,
        dc.content,
        dc.page_number,
        dc.chunk_index,
        1 - (dc.embedding <=> query_embedding) as similarity,
        d.filename,
        d.original_name,
        d.uploaded_at,
        LENGTH(dc.content) as chunk_length,
        dc.metadata
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE d.status = 'ready'
    AND dc.embedding IS NOT NULL
    AND dc.document_id = ANY(document_ids)
    AND 1 - (dc.embedding <=> query_embedding) > similarity_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
$function$;

-- Function to get context chunks around a specific chunk
CREATE OR REPLACE FUNCTION get_context_chunks(
    target_document_id uuid,
    target_chunk_index integer,
    context_window integer DEFAULT 1
)
RETURNS TABLE (
    id uuid,
    content text,
    page_number integer,
    chunk_index integer,
    metadata jsonb
)
LANGUAGE sql
STABLE
AS $function$
    SELECT 
        dc.id,
        dc.content,
        dc.page_number,
        dc.chunk_index,
        dc.metadata
    FROM document_chunks dc
    WHERE dc.document_id = target_document_id
    AND dc.chunk_index >= (target_chunk_index - context_window)
    AND dc.chunk_index <= (target_chunk_index + context_window)
    AND dc.chunk_index != target_chunk_index
    ORDER BY dc.chunk_index;
$function$;

-- Function for hybrid search (combining vector similarity with keyword matching)
CREATE OR REPLACE FUNCTION hybrid_search_chunks(
    query_embedding vector(768),
    query_text text,
    similarity_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10,
    keyword_boost float DEFAULT 0.1
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    content text,
    page_number integer,
    chunk_index integer,
    similarity float,
    keyword_score float,
    combined_score float,
    document_filename text,
    document_original_name text,
    metadata jsonb
)
LANGUAGE sql
STABLE
AS $function$
    WITH vector_results AS (
        SELECT 
            dc.id,
            dc.document_id,
            dc.content,
            dc.page_number,
            dc.chunk_index,
            1 - (dc.embedding <=> query_embedding) as similarity,
            d.filename,
            d.original_name,
            dc.metadata
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE d.status = 'ready'
        AND dc.embedding IS NOT NULL
        AND 1 - (dc.embedding <=> query_embedding) > similarity_threshold
    ),
    keyword_results AS (
        SELECT 
            vr.*,
            CASE 
                WHEN query_text = '' THEN 0
                ELSE ts_rank_cd(to_tsvector('english', vr.content), plainto_tsquery('english', query_text))
            END as keyword_score
        FROM vector_results vr
    )
    SELECT 
        kr.id,
        kr.document_id,
        kr.content,
        kr.page_number,
        kr.chunk_index,
        kr.similarity,
        kr.keyword_score,
        kr.similarity + (kr.keyword_score * keyword_boost) as combined_score,
        kr.filename,
        kr.original_name,
        kr.metadata
    FROM keyword_results kr
    ORDER BY combined_score DESC
    LIMIT match_count;
$function$;

-- Function to get search statistics
CREATE OR REPLACE FUNCTION get_search_statistics()
RETURNS TABLE (
    total_documents integer,
    ready_documents integer,
    total_chunks integer,
    chunks_with_embeddings integer,
    avg_chunk_length numeric,
    embedding_coverage_percent numeric
)
LANGUAGE sql
STABLE
AS $function$
    SELECT 
        (SELECT COUNT(*)::integer FROM documents) as total_documents,
        (SELECT COUNT(*)::integer FROM documents WHERE status = 'ready') as ready_documents,
        (SELECT COUNT(*)::integer FROM document_chunks) as total_chunks,
        (SELECT COUNT(*)::integer FROM document_chunks WHERE embedding IS NOT NULL) as chunks_with_embeddings,
        (SELECT ROUND(AVG(LENGTH(content)), 2) FROM document_chunks WHERE embedding IS NOT NULL) as avg_chunk_length,
        (SELECT ROUND(
            (COUNT(*) FILTER (WHERE embedding IS NOT NULL)::numeric / NULLIF(COUNT(*), 0)) * 100, 2
        ) FROM document_chunks) as embedding_coverage_percent;
$function$;

-- Create additional indexes for better search performance
CREATE INDEX IF NOT EXISTS idx_document_chunks_content_gin 
ON document_chunks USING gin(to_tsvector('english', content));

CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata_gin 
ON document_chunks USING gin(metadata);

CREATE INDEX IF NOT EXISTS idx_documents_status_uploaded_at 
ON documents(status, uploaded_at DESC);

-- Create a materialized view for search analytics (optional, for performance monitoring)
CREATE MATERIALIZED VIEW IF NOT EXISTS search_analytics AS
SELECT 
    d.id as document_id,
    d.filename,
    d.original_name,
    d.uploaded_at,
    COUNT(dc.id) as chunk_count,
    COUNT(dc.embedding) as embedded_chunks,
    AVG(LENGTH(dc.content)) as avg_chunk_length,
    MIN(dc.page_number) as first_page,
    MAX(dc.page_number) as last_page
FROM documents d
LEFT JOIN document_chunks dc ON d.id = dc.document_id
WHERE d.status = 'ready'
GROUP BY d.id, d.filename, d.original_name, d.uploaded_at;

-- Create index on the materialized view
CREATE INDEX IF NOT EXISTS idx_search_analytics_document_id 
ON search_analytics(document_id);

-- Function to refresh search analytics
CREATE OR REPLACE FUNCTION refresh_search_analytics()
RETURNS void
LANGUAGE sql
AS $function$
    REFRESH MATERIALIZED VIEW search_analytics;
$function$;

-- Add comments for documentation
COMMENT ON FUNCTION search_document_chunks(vector(768), float, int, uuid) IS 
'Enhanced vector similarity search with optional document filtering and performance optimizations';

COMMENT ON FUNCTION search_document_chunks_multi(vector(768), uuid[], float, int) IS 
'Vector similarity search across multiple specific documents';

COMMENT ON FUNCTION get_context_chunks(uuid, integer, integer) IS 
'Retrieve context chunks surrounding a target chunk for expanded search results';

COMMENT ON FUNCTION hybrid_search_chunks(vector(768), text, float, int, float) IS 
'Hybrid search combining vector similarity with keyword matching and boosting';

COMMENT ON FUNCTION get_search_statistics() IS 
'Get comprehensive statistics about the search index and document corpus';

COMMENT ON MATERIALIZED VIEW search_analytics IS 
'Materialized view providing analytics data for search performance monitoring';