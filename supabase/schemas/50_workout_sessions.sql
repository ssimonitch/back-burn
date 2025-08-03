-- =============================================================================
-- WORKOUT SESSIONS TABLE
-- =============================================================================
-- Individual workout instances with comprehensive performance and wellness tracking
-- Tracks actual workouts performed by users with RPE and mood data
-- =============================================================================

-- Workout_sessions table (actual workout instances) with enhanced tracking
CREATE TABLE IF NOT EXISTS public.workout_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    plan_id UUID REFERENCES public.plans(id) ON DELETE SET NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    notes TEXT,
    mood TEXT CHECK (mood IN ('great', 'good', 'neutral', 'tired', 'exhausted')),
    -- Enhanced tracking fields
    overall_rpe INTEGER CHECK (overall_rpe >= 1 AND overall_rpe <= 10),
    pre_workout_energy INTEGER CHECK (pre_workout_energy >= 1 AND pre_workout_energy <= 10),
    post_workout_energy INTEGER CHECK (post_workout_energy >= 1 AND post_workout_energy <= 10),
    workout_type TEXT CHECK (workout_type IN ('strength', 'hypertrophy', 'power', 'endurance', 'mixed', 'technique', 'deload')),
    -- Periodization enhancement
    training_phase TEXT CHECK (training_phase IN ('accumulation', 'intensification', 'realization', 'deload', 'testing')),
    total_volume DECIMAL(12,2),
    total_sets INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_workout_sessions_user_id ON public.workout_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_workout_sessions_plan_id ON public.workout_sessions(plan_id);
CREATE INDEX IF NOT EXISTS idx_workout_sessions_started_at ON public.workout_sessions(started_at DESC);

-- Enable RLS (policies defined in migrations)
ALTER TABLE public.workout_sessions ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE public.workout_sessions IS 'Individual workout instances with comprehensive performance and wellness tracking';
COMMENT ON COLUMN public.workout_sessions.plan_id IS 'Optional reference to workout plan being followed (null for ad-hoc workouts)';
COMMENT ON COLUMN public.workout_sessions.started_at IS 'When the workout session began (may differ from created_at)';
COMMENT ON COLUMN public.workout_sessions.completed_at IS 'When workout was finished - null indicates incomplete/ongoing session';
COMMENT ON COLUMN public.workout_sessions.mood IS 'Post-workout mood assessment for tracking training impact on wellbeing';
COMMENT ON COLUMN public.workout_sessions.overall_rpe IS 'Rate of Perceived Exertion (1-10) for entire workout session';
COMMENT ON COLUMN public.workout_sessions.pre_workout_energy IS 'Energy level before workout (1-10) for readiness correlation';
COMMENT ON COLUMN public.workout_sessions.post_workout_energy IS 'Energy level after workout (1-10) for recovery tracking';
COMMENT ON COLUMN public.workout_sessions.training_phase IS 'Current periodization phase for structured programming and progression tracking';
COMMENT ON COLUMN public.workout_sessions.total_volume IS 'Sum of all volume (weight × reps) for the session';
COMMENT ON COLUMN public.workout_sessions.total_sets IS 'Total number of sets performed in this session';