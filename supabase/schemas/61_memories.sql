-- =============================================================================
-- MEMORIES TABLE
-- =============================================================================
-- AI semantic memory store with vector embeddings for personalized context
-- Uses pgvector for similarity search to retrieve relevant conversation history
-- =============================================================================

-- Memories table (AI semantic memory with vector embeddings)
CREATE TABLE IF NOT EXISTS public.memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding extensions.halfvec(3072),
    memory_type TEXT CHECK (memory_type IN ('conversation', 'preference', 'goal', 'achievement', 'feedback')),
    importance_score DECIMAL(3,2) CHECK (importance_score >= 0 AND importance_score <= 1),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_memories_user_id ON public.memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_conversation_id ON public.memories(conversation_id);
CREATE INDEX IF NOT EXISTS idx_memories_memory_type ON public.memories(memory_type);

-- Vector similarity search index (HNSW method for better performance)
-- HNSW provides faster searches with better recall than IVFFlat for our use case
CREATE INDEX IF NOT EXISTS idx_memories_embedding ON public.memories 
    USING hnsw (embedding extensions.halfvec_l2_ops);

-- Enable RLS (policies defined in migrations)
ALTER TABLE public.memories ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- MEMORY-SPECIFIC FUNCTIONS
-- =============================================================================

-- Function to search memories by vector similarity
-- Returns memories similar to a query embedding for RAG context
-- SECURITY: Uses empty search_path to prevent search path manipulation attacks
CREATE OR REPLACE FUNCTION public.search_memories(
    p_user_id UUID,
    p_query_embedding extensions.halfvec(3072),
    p_limit INTEGER DEFAULT 10,
    p_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    memory_type TEXT,
    importance_score DECIMAL,
    similarity FLOAT,
    created_at TIMESTAMPTZ,
    metadata JSONB
) 
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.content,
        m.memory_type,
        m.importance_score,
        1 - (m.embedding OPERATOR(extensions.<=>) p_query_embedding) AS similarity,
        m.created_at,
        m.metadata
    FROM public.memories m
    WHERE m.user_id = p_user_id
        AND m.embedding IS NOT NULL
        AND 1 - (m.embedding OPERATOR(extensions.<=>) p_query_embedding) > p_threshold
    ORDER BY m.embedding OPERATOR(extensions.<=>) p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE public.memories IS 'AI semantic memory store with vector embeddings for personalized context retrieval';
COMMENT ON COLUMN public.memories.content IS 'Text content of the memory for semantic search and AI context';
COMMENT ON COLUMN public.memories.embedding IS 'Vector embedding of content for similarity search (3072 dimensions for gemini-embeddings-001)';
COMMENT ON COLUMN public.memories.memory_type IS 'Category of memory for filtering and importance weighting';
COMMENT ON COLUMN public.memories.importance_score IS 'Dynamic importance score from 0-1, may be updated based on relevance and recency';
COMMENT ON COLUMN public.memories.metadata IS 'Additional memory context like emotion, entities, or confidence scores';