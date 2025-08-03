-- =============================================================================
-- PLAN EXERCISES JUNCTION TABLE
-- =============================================================================
-- Defines exercises within workout plans and their programming parameters
-- Links plans to exercises with scheduling and set/rep schemes
-- =============================================================================

-- Plan_exercises junction table
CREATE TABLE IF NOT EXISTS public.plan_exercises (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES public.plans(id) ON DELETE CASCADE,
    exercise_id UUID NOT NULL REFERENCES public.exercises(id) ON DELETE CASCADE,
    day_of_week INTEGER NOT NULL CHECK (day_of_week >= 1 AND day_of_week <= 7),
    order_in_day INTEGER NOT NULL CHECK (order_in_day > 0),
    sets INTEGER NOT NULL CHECK (sets > 0),
    target_reps INTEGER[] NOT NULL,
    rest_seconds INTEGER CHECK (rest_seconds >= 0),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(plan_id, day_of_week, order_in_day)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_plan_exercises_plan_id ON public.plan_exercises(plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_exercises_exercise_id ON public.plan_exercises(exercise_id);
CREATE INDEX IF NOT EXISTS idx_plan_exercises_day ON public.plan_exercises(day_of_week);

-- Enable RLS (policies defined in migrations)
ALTER TABLE public.plan_exercises ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE public.plan_exercises IS 'Junction table defining exercises within workout plans and their programming parameters';
COMMENT ON COLUMN public.plan_exercises.day_of_week IS 'Day of week (1=Monday, 7=Sunday) when this exercise is scheduled';
COMMENT ON COLUMN public.plan_exercises.order_in_day IS 'Order of exercise within the workout session (1st, 2nd, 3rd, etc.)';
COMMENT ON COLUMN public.plan_exercises.target_reps IS 'Array of target rep ranges for each set (e.g., [8,10,12] for 3 sets)';
COMMENT ON COLUMN public.plan_exercises.rest_seconds IS 'Recommended rest period between sets in seconds';