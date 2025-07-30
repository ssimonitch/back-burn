-- MVP indexes and functions for Slow Burn schema
-- This file includes only essential indexes and functions needed for MVP functionality

-- =============================================================================
-- INDEXES FOR MVP PERFORMANCE
-- =============================================================================

-- Plans indexes - Essential for user's workout plans
CREATE INDEX idx_plans_user_id ON public.plans(user_id);

-- Workout sessions indexes - Essential for workout history
CREATE INDEX idx_workout_sessions_user_id ON public.workout_sessions(user_id);

-- Sets indexes - Essential for workout details and FK constraint performance
CREATE INDEX idx_sets_workout_session_id ON public.sets(workout_session_id);
CREATE INDEX idx_sets_exercise_id ON public.sets(exercise_id);

-- Memories indexes - Essential for AI functionality
CREATE INDEX idx_memories_user_id ON public.memories(user_id);
CREATE INDEX idx_memories_conversation_id ON public.memories(conversation_id);

-- Vector similarity search index (HNSW method for better performance)
CREATE INDEX idx_memories_embedding ON public.memories USING hnsw (embedding extensions.halfvec_l2_ops);

-- Conversations indexes - Essential for chat session queries
CREATE INDEX idx_conversations_user_id ON public.conversations(user_id);

-- Plan exercises indexes - Essential for loading workout plan details
CREATE INDEX idx_plan_exercises_plan_id ON public.plan_exercises(plan_id);
CREATE INDEX idx_plan_exercises_exercise_id ON public.plan_exercises(exercise_id);

-- Workout sessions indexes - Essential for plan tracking
CREATE INDEX idx_workout_sessions_plan_id ON public.workout_sessions(plan_id);

-- =============================================================================
-- DATABASE FUNCTIONS
-- =============================================================================

-- Function to increment user affinity score
-- SECURITY: Uses empty search_path to prevent search path manipulation attacks
CREATE OR REPLACE FUNCTION public.increment_affinity_score(p_user_id UUID, p_points INTEGER DEFAULT 1)
RETURNS INTEGER 
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    new_score INTEGER;
BEGIN
    UPDATE public.users 
    SET affinity_score = affinity_score + p_points
    WHERE id = p_user_id
    RETURNING affinity_score INTO new_score;
    
    RETURN new_score;
END;
$$ LANGUAGE plpgsql;

-- Function to search memories by vector similarity
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

