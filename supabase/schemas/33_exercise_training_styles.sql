-- =============================================================================
-- EXERCISE TRAINING STYLES JUNCTION TABLE
-- =============================================================================
-- Links exercises to training styles with suitability metrics
-- Helps recommend exercises based on training methodology
-- =============================================================================

-- Junction table linking exercises to training styles with suitability metrics
CREATE TABLE IF NOT EXISTS public.exercise_training_styles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exercise_id UUID NOT NULL REFERENCES public.exercises(id) ON DELETE CASCADE,
    training_style_id UUID NOT NULL REFERENCES public.training_styles(id) ON DELETE CASCADE,
    suitability_score INTEGER NOT NULL CHECK (suitability_score >= 1 AND suitability_score <= 5),
    optimal_rep_min INTEGER CHECK (optimal_rep_min > 0),
    optimal_rep_max INTEGER CHECK (optimal_rep_max > 0 AND optimal_rep_max >= optimal_rep_min),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(exercise_id, training_style_id)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_exercise_training_styles_exercise ON public.exercise_training_styles(exercise_id);
CREATE INDEX IF NOT EXISTS idx_exercise_training_styles_style ON public.exercise_training_styles(training_style_id);

-- Enable RLS (policies defined in migrations)
ALTER TABLE public.exercise_training_styles ENABLE ROW LEVEL SECURITY;

-- Comments
COMMENT ON TABLE public.exercise_training_styles IS 'Many-to-many relationship defining exercise suitability for different training styles';
COMMENT ON COLUMN public.exercise_training_styles.suitability_score IS 'How well-suited this exercise is for the training style (1=poor, 5=excellent)';
COMMENT ON COLUMN public.exercise_training_styles.optimal_rep_min IS 'Minimum recommended reps for this exercise in this training style';
COMMENT ON COLUMN public.exercise_training_styles.optimal_rep_max IS 'Maximum recommended reps for this exercise in this training style';
COMMENT ON COLUMN public.exercise_training_styles.notes IS 'Additional notes about using this exercise in this training style';