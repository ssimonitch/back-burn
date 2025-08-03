-- =============================================================================
-- EXERCISE MUSCLES JUNCTION TABLE
-- =============================================================================
-- Many-to-many relationship defining which muscles are worked by each exercise
-- Includes muscle role (primary, secondary, stabilizer) and activation level
-- =============================================================================

-- Junction table for exercise muscle groups (many-to-many with role)
CREATE TABLE IF NOT EXISTS public.exercise_muscles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exercise_id UUID NOT NULL REFERENCES public.exercises(id) ON DELETE CASCADE,
    muscle_group_id UUID NOT NULL REFERENCES public.muscle_groups(id) ON DELETE CASCADE,
    muscle_role TEXT NOT NULL CHECK (muscle_role IN ('primary', 'secondary', 'stabilizer')),
    activation_level INTEGER CHECK (activation_level >= 1 AND activation_level <= 5),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(exercise_id, muscle_group_id)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_exercise_muscles_exercise ON public.exercise_muscles(exercise_id);
CREATE INDEX IF NOT EXISTS idx_exercise_muscles_muscle ON public.exercise_muscles(muscle_group_id);
CREATE INDEX IF NOT EXISTS idx_exercise_muscles_role ON public.exercise_muscles(muscle_role);

-- Enable RLS (policies defined in migrations)
ALTER TABLE public.exercise_muscles ENABLE ROW LEVEL SECURITY;

-- Comments
COMMENT ON TABLE public.exercise_muscles IS 'Many-to-many relationship defining which muscles are worked by each exercise and their roles';
COMMENT ON COLUMN public.exercise_muscles.muscle_role IS 'Role of muscle group in exercise - primary mover, secondary mover, or stabilizer';
COMMENT ON COLUMN public.exercise_muscles.activation_level IS 'Relative activation level from 1 (minimal) to 5 (maximal) for exercise programming';