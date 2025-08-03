-- =============================================================================
-- EXERCISES TABLE
-- =============================================================================
-- Comprehensive exercise database with detailed biomechanical classifications
-- Central to the workout planning and tracking system
-- =============================================================================

-- Enhanced exercises table with comprehensive classification
CREATE TABLE IF NOT EXISTS public.exercises (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    instructions TEXT[],
    tips TEXT[],
    -- Enhanced classification fields
    primary_equipment_id UUID REFERENCES public.equipment_types(id) ON DELETE SET NULL,
    secondary_equipment_id UUID REFERENCES public.equipment_types(id) ON DELETE SET NULL,
    force_vector TEXT CHECK (force_vector IN ('vertical', 'horizontal', 'lateral', 'rotational', 'multi_planar')),
    exercise_category TEXT CHECK (exercise_category IN ('strength', 'cardio', 'mobility', 'plyometric', 'sport_specific', 'corrective', 'balance', 'hypertrophy')),
    mechanic_type TEXT CHECK (mechanic_type IN ('compound', 'isolation', 'hybrid')),
    body_region TEXT CHECK (body_region IN ('upper', 'lower', 'full_body', 'core')),
    difficulty_level TEXT CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
    -- Unilateral/bilateral classification
    laterality TEXT CHECK (laterality IN ('bilateral', 'unilateral_left', 'unilateral_right', 'unilateral_alternating')),
    -- Load type
    load_type TEXT CHECK (load_type IN ('external', 'bodyweight', 'assisted', 'weighted_bodyweight')),
    -- Metadata for future expansion
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, primary_equipment_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_exercises_primary_equipment ON public.exercises(primary_equipment_id);
CREATE INDEX IF NOT EXISTS idx_exercises_body_region ON public.exercises(body_region);
CREATE INDEX IF NOT EXISTS idx_exercises_category ON public.exercises(exercise_category);

-- Enable RLS (policies defined in migrations)
ALTER TABLE public.exercises ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE public.exercises IS 'Comprehensive exercise database with detailed biomechanical and training classifications';
COMMENT ON COLUMN public.exercises.force_vector IS 'Primary direction of force application during the exercise movement';
COMMENT ON COLUMN public.exercises.mechanic_type IS 'Joint involvement classification - compound (multi-joint), isolation (single-joint), or hybrid';
COMMENT ON COLUMN public.exercises.laterality IS 'Whether exercise is performed bilaterally or unilaterally (one side at a time)';
COMMENT ON COLUMN public.exercises.load_type IS 'Type of resistance used - external weights, bodyweight, or assisted variations';
COMMENT ON COLUMN public.exercises.metadata IS 'Extensible JSON object for future exercise data and integrations';