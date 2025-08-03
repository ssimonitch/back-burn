-- =============================================================================
-- SETS TABLE
-- =============================================================================
-- Individual exercise sets with detailed performance metrics
-- Most granular level of workout tracking with comprehensive data capture
-- =============================================================================

-- Enhanced sets table with comprehensive performance tracking
CREATE TABLE IF NOT EXISTS public.sets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workout_session_id UUID NOT NULL REFERENCES public.workout_sessions(id) ON DELETE CASCADE,
    exercise_id UUID NOT NULL REFERENCES public.exercises(id) ON DELETE CASCADE,
    set_number INTEGER NOT NULL CHECK (set_number > 0),
    -- Basic performance data
    weight DECIMAL(10,2) CHECK (weight >= 0),
    reps INTEGER NOT NULL CHECK (reps > 0),
    rest_taken_seconds INTEGER CHECK (rest_taken_seconds >= 0),
    rpe INTEGER CHECK (rpe >= 1 AND rpe <= 10),
    -- Enhanced performance tracking
    volume_load DECIMAL(12,2) GENERATED ALWAYS AS (weight * reps) STORED,
    tempo TEXT, -- Format: "3-1-2-1" (eccentric-pause-concentric-pause in seconds)
    range_of_motion_quality TEXT CHECK (range_of_motion_quality IN ('full', 'partial', 'limited', 'assisted')),
    form_quality INTEGER CHECK (form_quality >= 1 AND form_quality <= 5),
    -- Intensity tracking
    estimated_1rm DECIMAL(10,2),
    intensity_percentage DECIMAL(5,2) CHECK (intensity_percentage >= 0 AND intensity_percentage <= 200),
    -- Set type classification
    set_type TEXT CHECK (set_type IN ('working', 'warmup', 'backoff', 'drop', 'cluster', 'rest_pause', 'amrap')),
    -- Failure tracking
    reps_in_reserve INTEGER CHECK (reps_in_reserve >= 0),
    reached_failure BOOLEAN DEFAULT false,
    failure_type TEXT CHECK (failure_type IN ('muscular', 'form', 'cardiovascular', 'motivation')),
    -- Environment and conditions
    equipment_variation TEXT,
    assistance_type TEXT CHECK (assistance_type IN ('none', 'spotter', 'machine_assist', 'band_assist')),
    -- Notes and feedback
    notes TEXT,
    technique_cues TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sets_workout_session_id ON public.sets(workout_session_id);
CREATE INDEX IF NOT EXISTS idx_sets_exercise_id ON public.sets(exercise_id);
CREATE INDEX IF NOT EXISTS idx_sets_set_type ON public.sets(set_type);

-- Enable RLS (policies defined in migrations)
ALTER TABLE public.sets ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE public.sets IS 'Individual exercise sets with detailed performance metrics for progression tracking and analysis';
COMMENT ON COLUMN public.sets.set_number IS 'Order of this set within the exercise (1st set, 2nd set, etc.)';
COMMENT ON COLUMN public.sets.volume_load IS 'Calculated field: weight × reps, automatically updated';
COMMENT ON COLUMN public.sets.tempo IS 'Tempo notation in format "eccentric-pause-concentric-pause" (e.g., "3-1-2-1")';
COMMENT ON COLUMN public.sets.range_of_motion_quality IS 'Assessment of range of motion achieved during the set';
COMMENT ON COLUMN public.sets.form_quality IS 'Subjective form quality rating from 1 (poor) to 5 (perfect)';
COMMENT ON COLUMN public.sets.estimated_1rm IS 'Calculated or estimated one-rep max based on weight and reps performed';
COMMENT ON COLUMN public.sets.intensity_percentage IS 'Percentage of estimated 1RM used for this set';
COMMENT ON COLUMN public.sets.set_type IS 'Classification of set purpose within workout programming';
COMMENT ON COLUMN public.sets.reps_in_reserve IS 'Estimated reps remaining before failure (RIR) for autoregulation';
COMMENT ON COLUMN public.sets.failure_type IS 'Type of failure reached if set was taken to failure';
COMMENT ON COLUMN public.sets.equipment_variation IS 'Specific equipment variation used (e.g., "close_grip", "wide_stance")';
COMMENT ON COLUMN public.sets.technique_cues IS 'Array of coaching cues or technical notes for this set';