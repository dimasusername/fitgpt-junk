-- Initial database schema for AI Chat Application
-- This migration creates the core tables and sets up pgvector extension

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sources JSONB DEFAULT NULL,
    agent_info JSONB DEFAULT NULL
);

-- Documents table (references Supabase Storage)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename TEXT NOT NULL,
    original_name TEXT NOT NULL,
    storage_path TEXT NOT NULL,  -- Supabase Storage path
    public_url TEXT,             -- CDN URL for file access
    mime_type TEXT NOT NULL DEFAULT 'application/pdf',
    size INTEGER NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL CHECK (status IN ('processing', 'ready', 'error')) DEFAULT 'processing',
    chunk_count INTEGER DEFAULT 0
);

-- Document chunks table with pgvector embeddings
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(768), -- Google text-embedding-004 dimension
    page_number INTEGER,
    chunk_index INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX idx_conversations_updated_at ON conversations(updated_at DESC);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX idx_messages_role ON messages(role);

CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at DESC);
CREATE INDEX idx_documents_filename ON documents(filename);

CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_chunk_index ON document_chunks(document_id, chunk_index);
CREATE INDEX idx_document_chunks_page_number ON document_chunks(page_number);

-- Create vector index for similarity search using HNSW algorithm
-- This provides fast approximate nearest neighbor search
CREATE INDEX idx_document_chunks_embedding ON document_chunks 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at for conversations
CREATE TRIGGER update_conversations_updated_at 
    BEFORE UPDATE ON conversations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Function for vector similarity search
CREATE OR REPLACE FUNCTION search_document_chunks(
    query_embedding vector(768),
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
    document_original_name text
)
LANGUAGE sql
STABLE
AS $$
    SELECT 
        dc.id,
        dc.document_id,
        dc.content,
        dc.page_number,
        dc.chunk_index,
        1 - (dc.embedding <=> query_embedding) as similarity,
        d.filename,
        d.original_name
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE d.status = 'ready'
    AND 1 - (dc.embedding <=> query_embedding) > similarity_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Create RLS (Row Level Security) policies for basic security
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- For now, allow all operations (can be restricted later based on user authentication)
CREATE POLICY "Allow all operations on conversations" ON conversations FOR ALL USING (true);
CREATE POLICY "Allow all operations on messages" ON messages FOR ALL USING (true);
CREATE POLICY "Allow all operations on documents" ON documents FOR ALL USING (true);
CREATE POLICY "Allow all operations on document_chunks" ON document_chunks FOR ALL USING (true);