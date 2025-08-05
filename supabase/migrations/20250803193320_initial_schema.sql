-- =============================================================================
-- EXTENSIONS SETUP
-- =============================================================================
-- PostgreSQL extensions required for the Slow Burn application
-- This must be loaded first as other schemas depend on these extensions
-- =============================================================================

-- Create a dedicated schema for extensions to avoid polluting the public schema
CREATE SCHEMA IF NOT EXISTS extensions;

-- Grant usage on extensions schema to authenticated users
-- This allows users to use the vector types and functions
GRANT USAGE ON SCHEMA extensions TO authenticated;
GRANT USAGE ON SCHEMA extensions TO service_role;

-- Enable UUID extension in public schema (standard practice for uuid-ossp)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;

-- Enable vector extension in dedicated extensions schema for security
-- This prevents namespace pollution and provides better security boundaries
CREATE EXTENSION IF NOT EXISTS "vector" WITH SCHEMA extensions;

-- Comment on the extensions schema
COMMENT ON SCHEMA extensions IS 'Dedicated schema for PostgreSQL extensions to maintain security isolation';

-- =============================================================================
-- MOVEMENT PATTERNS TABLE
-- =============================================================================
-- Reference table for fundamental movement patterns used in exercise classification
-- Examples: squat, hinge, push, pull, carry, gait
-- =============================================================================

-- Movement patterns lookup table
CREATE TABLE IF NOT EXISTS public.movement_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS (policies defined in migrations)
ALTER TABLE public.movement_patterns ENABLE ROW LEVEL SECURITY;

-- Comments
COMMENT ON TABLE public.movement_patterns IS 'Reference table for fundamental movement patterns (e.g., squat, hinge, push, pull, carry, gait)';
COMMENT ON COLUMN public.movement_patterns.name IS 'Unique identifier for the movement pattern (e.g., "squat", "hip_hinge")';
COMMENT ON COLUMN public.movement_patterns.description IS 'Detailed explanation of the movement pattern and its characteristics';

-- =============================================================================
-- MUSCLE GROUPS TABLE
-- =============================================================================
-- Reference table for muscle groups used in exercise classification and targeting
-- Includes anatomical regions for workout organization
-- =============================================================================

-- Muscle groups lookup table  
CREATE TABLE IF NOT EXISTS public.muscle_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    muscle_region TEXT NOT NULL CHECK (muscle_region IN ('upper', 'lower', 'core', 'full_body', 'posterior_chain')),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS (policies defined in migrations)
ALTER TABLE public.muscle_groups ENABLE ROW LEVEL SECURITY;

-- Comments
COMMENT ON TABLE public.muscle_groups IS 'Reference table for muscle groups used in exercise classification and targeting';
COMMENT ON COLUMN public.muscle_groups.name IS 'Name of the muscle group (e.g., "quadriceps", "latissimus_dorsi")';
COMMENT ON COLUMN public.muscle_groups.muscle_region IS 'Broad anatomical region classification for workout organization';
COMMENT ON COLUMN public.muscle_groups.description IS 'Anatomical description and function of the muscle group';

-- =============================================================================
-- EQUIPMENT TYPES TABLE
-- =============================================================================
-- Reference table for gym equipment and tools used in exercises
-- Categorized for filtering and organization
-- =============================================================================

-- Equipment types lookup table
CREATE TABLE IF NOT EXISTS public.equipment_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    category TEXT CHECK (category IN ('free_weight', 'machine', 'bodyweight', 'cable', 'other')),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS (policies defined in migrations)
ALTER TABLE public.equipment_types ENABLE ROW LEVEL SECURITY;

-- Comments
COMMENT ON TABLE public.equipment_types IS 'Reference table for gym equipment and tools used in exercises';
COMMENT ON COLUMN public.equipment_types.name IS 'Specific equipment name (e.g., "barbell", "dumbbell", "lat_pulldown_machine")';
COMMENT ON COLUMN public.equipment_types.category IS 'High-level equipment classification for filtering and organization';
COMMENT ON COLUMN public.equipment_types.description IS 'Details about the equipment, usage notes, and variations';

-- =============================================================================
-- TRAINING STYLES TABLE
-- =============================================================================
-- Reference table for different training methodologies and their characteristics
-- Used for exercise classification and programming recommendations
-- =============================================================================

-- Training styles reference table for exercise classification
CREATE TABLE IF NOT EXISTS public.training_styles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    typical_rep_range TEXT, -- e.g., "1-6", "6-12", "8-15"
    typical_set_range TEXT, -- e.g., "3-5", "3-6", "2-4"
    rest_periods TEXT, -- e.g., "3-5 minutes", "90-180 seconds"
    focus_description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS (policies defined in migrations)
ALTER TABLE public.training_styles ENABLE ROW LEVEL SECURITY;

-- Comments
COMMENT ON TABLE public.training_styles IS 'Reference table for different training methodologies and their characteristics';
COMMENT ON COLUMN public.training_styles.name IS 'Training style identifier (e.g., "powerlifting", "bodybuilding", "powerbuilding")';
COMMENT ON COLUMN public.training_styles.typical_rep_range IS 'Common rep ranges used in this training style';
COMMENT ON COLUMN public.training_styles.typical_set_range IS 'Common set ranges used in this training style';
COMMENT ON COLUMN public.training_styles.rest_periods IS 'Typical rest periods between sets for this training style';
COMMENT ON COLUMN public.training_styles.focus_description IS 'Primary focus and goals of this training methodology';

-- =============================================================================
-- PROFILES TABLE
-- =============================================================================
-- User profiles extending Supabase auth with fitness-specific data
-- Tracks user preferences, goals, and AI companion affinity score
-- =============================================================================

-- Profiles table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT,
    age INTEGER CHECK (age >= 13 AND age <= 120),
    fitness_level TEXT CHECK (fitness_level IN ('beginner', 'intermediate', 'advanced')),
    goals TEXT[],
    preferences JSONB DEFAULT '{}',
    affinity_score INTEGER DEFAULT 0 CHECK (affinity_score >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS (policies defined in migrations)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- PROFILE-SPECIFIC FUNCTIONS
-- =============================================================================

-- Function to handle new user creation from auth.users
-- Automatically creates a profile entry when a new user signs up
-- SECURITY: Uses empty search_path to prevent search path manipulation attacks
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    INSERT INTO public.profiles (id, username, full_name)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1)),
        COALESCE(NEW.raw_user_meta_data->>'full_name', '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on auth.users to automatically create profile entries
-- Note: This trigger must be recreated if auth schema is reset
CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to increment user affinity score
-- Used when users complete workouts or have positive AI interactions
-- SECURITY: Uses empty search_path to prevent search path manipulation attacks
CREATE OR REPLACE FUNCTION public.increment_affinity_score(p_user_id UUID, p_points INTEGER DEFAULT 1)
RETURNS INTEGER 
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    new_score INTEGER;
BEGIN
    UPDATE public.profiles 
    SET affinity_score = affinity_score + p_points
    WHERE id = p_user_id
    RETURNING affinity_score INTO new_score;
    
    RETURN new_score;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE public.profiles IS 'User profiles extending Supabase auth with fitness-specific data and AI companion affinity';
COMMENT ON COLUMN public.profiles.id IS 'Foreign key to auth.users - same user across Supabase auth and application';
COMMENT ON COLUMN public.profiles.username IS 'Unique display name chosen by user for app identification';
COMMENT ON COLUMN public.profiles.affinity_score IS 'Tracks user engagement with AI companion, incremented by workout completion and positive interactions';
COMMENT ON COLUMN public.profiles.goals IS 'Array of user fitness goals (e.g., "lose_weight", "build_muscle", "improve_endurance")';
COMMENT ON COLUMN public.profiles.preferences IS 'JSONB object storing user preferences for workouts, AI personality, units, etc.';
COMMENT ON COLUMN public.profiles.fitness_level IS 'Self-reported fitness level used for exercise and plan recommendations';

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

-- =============================================================================
-- PLANS TABLE
-- =============================================================================
-- Versioned workout plan templates that can be followed by users or shared publicly
-- Plans are immutable once created - modifications create new versions
-- =============================================================================

-- Plans table (workout plan templates)
CREATE TABLE IF NOT EXISTS public.plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    training_style TEXT REFERENCES public.training_styles(name) ON DELETE RESTRICT,
    goal TEXT,
    difficulty_level TEXT CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    duration_weeks INTEGER CHECK (duration_weeks > 0),
    days_per_week INTEGER CHECK (days_per_week >= 1 AND days_per_week <= 7),
    is_public BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}',
    -- Versioning fields for immutable plan history
    version_number INTEGER NOT NULL DEFAULT 1,
    parent_plan_id UUID REFERENCES public.plans(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ DEFAULT NULL,
    -- Ensure unique versioning per user and plan name
    UNIQUE(user_id, name, version_number)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_plans_user_id ON public.plans(user_id);
CREATE INDEX IF NOT EXISTS idx_plans_is_public ON public.plans(is_public) WHERE is_public = true;
CREATE INDEX IF NOT EXISTS idx_plans_parent ON public.plans(parent_plan_id);
CREATE INDEX IF NOT EXISTS idx_plans_training_style ON public.plans(training_style);
CREATE INDEX IF NOT EXISTS idx_plans_deleted_at ON public.plans(deleted_at) WHERE deleted_at IS NULL;

-- Enable RLS (policies defined in migrations)
ALTER TABLE public.plans ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE public.plans IS 'Versioned workout plan templates that can be followed by users or shared publicly. Plans are immutable once created - modifications create new versions.';
COMMENT ON COLUMN public.plans.training_style IS 'Primary training style/methodology for this plan (references training_styles.name)';
COMMENT ON COLUMN public.plans.goal IS 'Primary training goal this plan targets (e.g., "strength", "hypertrophy", "weight_loss")';
COMMENT ON COLUMN public.plans.duration_weeks IS 'Planned duration in weeks before progression or plan change';
COMMENT ON COLUMN public.plans.days_per_week IS 'Intended training frequency per week';
COMMENT ON COLUMN public.plans.is_public IS 'Whether this plan can be discovered and used by other users';
COMMENT ON COLUMN public.plans.metadata IS 'Additional plan configuration like periodization, rest weeks, deload protocols';
COMMENT ON COLUMN public.plans.version_number IS 'Version number for this plan iteration (increments with each modification)';
COMMENT ON COLUMN public.plans.parent_plan_id IS 'References the original plan this version derives from (NULL for v1)';
COMMENT ON COLUMN public.plans.is_active IS 'Whether this is the current active version of the plan (only one version per plan name should be active)';
COMMENT ON COLUMN public.plans.deleted_at IS 'Timestamp when plan was soft-deleted. NULL means plan is active/not deleted.';

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

-- =============================================================================
-- MEMORIES TABLE
-- =============================================================================
-- AI semantic memory store with vector embeddings for personalized context
-- Uses pgvector for similarity search to retrieve relevant conversation history
-- =============================================================================

-- Memories table (AI semantic memory with vector embeddings)
CREATE TABLE IF NOT EXISTS public.memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding extensions.halfvec(3072),
    memory_type TEXT CHECK (memory_type IN ('conversation', 'preference', 'goal', 'achievement', 'feedback')),
    importance_score DECIMAL(3,2) CHECK (importance_score >= 0 AND importance_score <= 1),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_memories_user_id ON public.memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_conversation_id ON public.memories(conversation_id);
CREATE INDEX IF NOT EXISTS idx_memories_memory_type ON public.memories(memory_type);

-- Vector similarity search index (HNSW method for better performance)
-- HNSW provides faster searches with better recall than IVFFlat for our use case
CREATE INDEX IF NOT EXISTS idx_memories_embedding ON public.memories 
    USING hnsw (embedding extensions.halfvec_l2_ops);

-- Enable RLS (policies defined in migrations)
ALTER TABLE public.memories ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- MEMORY-SPECIFIC FUNCTIONS
-- =============================================================================

-- Function to search memories by vector similarity
-- Returns memories similar to a query embedding for RAG context
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

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE public.memories IS 'AI semantic memory store with vector embeddings for personalized context retrieval';
COMMENT ON COLUMN public.memories.content IS 'Text content of the memory for semantic search and AI context';
COMMENT ON COLUMN public.memories.embedding IS 'Vector embedding of content for similarity search (3072 dimensions for gemini-embeddings-001)';
COMMENT ON COLUMN public.memories.memory_type IS 'Category of memory for filtering and importance weighting';
COMMENT ON COLUMN public.memories.importance_score IS 'Dynamic importance score from 0-1, may be updated based on relevance and recency';
COMMENT ON COLUMN public.memories.metadata IS 'Additional memory context like emotion, entities, or confidence scores';

-- =============================================================================
-- SHARED FUNCTIONS
-- =============================================================================
-- Cross-table utility functions used by multiple tables
-- Includes timestamp management and other shared functionality
-- =============================================================================

-- Function to automatically update updated_at timestamp
-- Used by multiple tables that track modification times
-- SECURITY: Uses empty search_path to prevent search path manipulation attacks
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER 
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION public.update_updated_at_column() IS 'Trigger function to automatically update the updated_at timestamp when a row is modified';

-- =============================================================================
-- SHARED TRIGGERS
-- =============================================================================
-- Triggers that apply to multiple tables
-- Centralized for easier maintenance and overview
-- =============================================================================

-- =============================================================================
-- UPDATED_AT TRIGGERS
-- =============================================================================
-- Automatically update the updated_at timestamp when rows are modified

CREATE TRIGGER update_profiles_updated_at 
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_exercises_updated_at 
    BEFORE UPDATE ON public.exercises
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_workout_sessions_updated_at 
    BEFORE UPDATE ON public.workout_sessions
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_sets_updated_at 
    BEFORE UPDATE ON public.sets
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at 
    BEFORE UPDATE ON public.conversations
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_memories_updated_at 
    BEFORE UPDATE ON public.memories
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();