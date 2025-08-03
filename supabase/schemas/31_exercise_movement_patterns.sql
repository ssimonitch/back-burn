-- =============================================================================
-- EXERCISE MOVEMENT PATTERNS JUNCTION TABLE
-- =============================================================================
-- Many-to-many relationship between exercises and fundamental movement patterns
-- Allows exercises to be classified by multiple movement patterns
-- =============================================================================

-- Junction table for exercise movement patterns (many-to-many)
CREATE TABLE IF NOT EXISTS public.exercise_movement_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exercise_id UUID NOT NULL REFERENCES public.exercises(id) ON DELETE CASCADE,
    movement_pattern_id UUID NOT NULL REFERENCES public.movement_patterns(id) ON DELETE CASCADE,
    is_primary BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(exercise_id, movement_pattern_id)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_exercise_movement_patterns_exercise ON public.exercise_movement_patterns(exercise_id);
CREATE INDEX IF NOT EXISTS idx_exercise_movement_patterns_pattern ON public.exercise_movement_patterns(movement_pattern_id);

-- Enable RLS (policies defined in migrations)
ALTER TABLE public.exercise_movement_patterns ENABLE ROW LEVEL SECURITY;

-- Comments
COMMENT ON TABLE public.exercise_movement_patterns IS 'Many-to-many relationship between exercises and fundamental movement patterns';
COMMENT ON COLUMN public.exercise_movement_patterns.is_primary IS 'Whether this is the primary movement pattern for the exercise (vs secondary/accessory pattern)';