-- =============================================================================
-- EXERCISE RELATIONSHIPS TABLE
-- =============================================================================
-- Defines relationships between exercises for programming and progression
-- Includes variations, progressions, regressions, alternatives, and pairings
-- =============================================================================

-- Exercise variations/alternatives relationship
CREATE TABLE IF NOT EXISTS public.exercise_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_exercise_id UUID NOT NULL REFERENCES public.exercises(id) ON DELETE CASCADE,
    related_exercise_id UUID NOT NULL REFERENCES public.exercises(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL CHECK (relationship_type IN ('variation', 'progression', 'regression', 'alternative', 'antagonist', 'superset')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(parent_exercise_id, related_exercise_id, relationship_type),
    CHECK (parent_exercise_id != related_exercise_id)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_exercise_relationships_parent ON public.exercise_relationships(parent_exercise_id);
CREATE INDEX IF NOT EXISTS idx_exercise_relationships_related ON public.exercise_relationships(related_exercise_id);
CREATE INDEX IF NOT EXISTS idx_exercise_relationships_type ON public.exercise_relationships(relationship_type);

-- Enable RLS (policies defined in migrations)
ALTER TABLE public.exercise_relationships ENABLE ROW LEVEL SECURITY;

-- Comments
COMMENT ON TABLE public.exercise_relationships IS 'Defines relationships between exercises for programming and progression recommendations';
COMMENT ON COLUMN public.exercise_relationships.relationship_type IS 'Type of relationship - variation, progression/regression, alternative, antagonist pair, or superset pairing';
COMMENT ON COLUMN public.exercise_relationships.notes IS 'Additional context about when to use this relationship (e.g., equipment substitution, injury modification)';