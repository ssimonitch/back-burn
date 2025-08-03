-- =============================================================================
-- CONVERSATIONS TABLE
-- =============================================================================
-- AI chat session boundaries and context for managing conversation history
-- Tracks conversation sessions with the AI fitness companion
-- =============================================================================

-- Conversations table (AI chat sessions)
CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON public.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_started_at ON public.conversations(started_at DESC);

-- Enable RLS (policies defined in migrations)
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE public.conversations IS 'AI chat session boundaries and context for managing conversation history and state';
COMMENT ON COLUMN public.conversations.started_at IS 'When the conversation session began (first message timestamp)';
COMMENT ON COLUMN public.conversations.ended_at IS 'When the conversation session ended (null for ongoing conversations)';
COMMENT ON COLUMN public.conversations.context IS 'Session context like conversation summary, user goals, or AI personality state';