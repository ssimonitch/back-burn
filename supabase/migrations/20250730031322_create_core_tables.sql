-- Core database tables for Slow Burn fitness application
-- This file creates all core tables in proper dependency order
--
-- TIMESTAMP STRATEGY:
-- - created_at: All tables have this for audit trail and data lifecycle management
-- - updated_at: Only on tables with mutable user data that might be corrected/modified
--   * User profiles and preferences (users)
--   * User-created content that can be edited (exercises)
--   * Workout data that users might correct (sets, workout_sessions)
--   * Media/content with editable metadata (conversations)
--   * AI data that evolves over time (memories)
-- - Reference tables, junction tables, historical snapshots, and versioned data use only created_at
--   as they represent immutable data or point-in-time records
-- - Plans use versioning strategy: new versions are created instead of updating existing records

-- =============================================================================
-- UTILITY FUNCTIONS
-- =============================================================================

-- Function to automatically update updated_at timestamp
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

-- =============================================================================
-- REFERENCE TABLES (no dependencies)
-- =============================================================================

-- Movement patterns lookup table
CREATE TABLE IF NOT EXISTS public.movement_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.movement_patterns IS 'Reference table for fundamental movement patterns (e.g., squat, hinge, push, pull, carry, gait)';
COMMENT ON COLUMN public.movement_patterns.name IS 'Unique identifier for the movement pattern (e.g., "squat", "hip_hinge")';
COMMENT ON COLUMN public.movement_patterns.description IS 'Detailed explanation of the movement pattern and its characteristics';

-- Muscle groups lookup table  
CREATE TABLE IF NOT EXISTS public.muscle_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    muscle_region TEXT NOT NULL CHECK (muscle_region IN ('upper', 'lower', 'core', 'full_body', 'posterior_chain')),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.muscle_groups IS 'Reference table for muscle groups used in exercise classification and targeting';
COMMENT ON COLUMN public.muscle_groups.name IS 'Name of the muscle group (e.g., "quadriceps", "latissimus_dorsi")';
COMMENT ON COLUMN public.muscle_groups.muscle_region IS 'Broad anatomical region classification for workout organization';
COMMENT ON COLUMN public.muscle_groups.description IS 'Anatomical description and function of the muscle group';

-- Equipment types lookup table
CREATE TABLE IF NOT EXISTS public.equipment_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    category TEXT CHECK (category IN ('free_weight', 'machine', 'bodyweight', 'cable', 'other')),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.equipment_types IS 'Reference table for gym equipment and tools used in exercises';
COMMENT ON COLUMN public.equipment_types.name IS 'Specific equipment name (e.g., "barbell", "dumbbell", "lat_pulldown_machine")';
COMMENT ON COLUMN public.equipment_types.category IS 'High-level equipment classification for filtering and organization';
COMMENT ON COLUMN public.equipment_types.description IS 'Details about the equipment, usage notes, and variations';

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

COMMENT ON TABLE public.training_styles IS 'Reference table for different training methodologies and their characteristics';
COMMENT ON COLUMN public.training_styles.name IS 'Training style identifier (e.g., "powerlifting", "bodybuilding", "powerbuilding")';
COMMENT ON COLUMN public.training_styles.typical_rep_range IS 'Common rep ranges used in this training style';
COMMENT ON COLUMN public.training_styles.typical_set_range IS 'Common set ranges used in this training style';
COMMENT ON COLUMN public.training_styles.rest_periods IS 'Typical rest periods between sets for this training style';
COMMENT ON COLUMN public.training_styles.focus_description IS 'Primary focus and goals of this training methodology';

-- =============================================================================
-- CORE USER TABLES
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

COMMENT ON TABLE public.profiles IS 'User profiles extending Supabase auth with fitness-specific data and AI companion affinity';
COMMENT ON COLUMN public.profiles.id IS 'Foreign key to auth.users - same user across Supabase auth and application';
COMMENT ON COLUMN public.profiles.username IS 'Unique display name chosen by user for app identification';
COMMENT ON COLUMN public.profiles.affinity_score IS 'Tracks user engagement with AI companion, incremented by workout completion and positive interactions';
COMMENT ON COLUMN public.profiles.goals IS 'Array of user fitness goals (e.g., "lose_weight", "build_muscle", "improve_endurance")';
COMMENT ON COLUMN public.profiles.preferences IS 'JSONB object storing user preferences for workouts, AI personality, units, etc.';
COMMENT ON COLUMN public.profiles.fitness_level IS 'Self-reported fitness level used for exercise and plan recommendations';

-- =============================================================================
-- ENHANCED EXERCISE SYSTEM
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

COMMENT ON TABLE public.exercises IS 'Comprehensive exercise database with detailed biomechanical and training classifications';
COMMENT ON COLUMN public.exercises.force_vector IS 'Primary direction of force application during the exercise movement';
COMMENT ON COLUMN public.exercises.mechanic_type IS 'Joint involvement classification - compound (multi-joint), isolation (single-joint), or hybrid';
COMMENT ON COLUMN public.exercises.laterality IS 'Whether exercise is performed bilaterally or unilaterally (one side at a time)';
COMMENT ON COLUMN public.exercises.load_type IS 'Type of resistance used - external weights, bodyweight, or assisted variations';
COMMENT ON COLUMN public.exercises.metadata IS 'Extensible JSON object for future exercise data and integrations';

-- Junction table for exercise movement patterns (many-to-many)
CREATE TABLE IF NOT EXISTS public.exercise_movement_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exercise_id UUID NOT NULL REFERENCES public.exercises(id) ON DELETE CASCADE,
    movement_pattern_id UUID NOT NULL REFERENCES public.movement_patterns(id) ON DELETE CASCADE,
    is_primary BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(exercise_id, movement_pattern_id)
);

COMMENT ON TABLE public.exercise_movement_patterns IS 'Many-to-many relationship between exercises and fundamental movement patterns';
COMMENT ON COLUMN public.exercise_movement_patterns.is_primary IS 'Whether this is the primary movement pattern for the exercise (vs secondary/accessory pattern)';

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

COMMENT ON TABLE public.exercise_training_styles IS 'Many-to-many relationship defining exercise suitability for different training styles';
COMMENT ON COLUMN public.exercise_training_styles.suitability_score IS 'How well-suited this exercise is for the training style (1=poor, 5=excellent)';
COMMENT ON COLUMN public.exercise_training_styles.optimal_rep_min IS 'Minimum recommended reps for this exercise in this training style';
COMMENT ON COLUMN public.exercise_training_styles.optimal_rep_max IS 'Maximum recommended reps for this exercise in this training style';
COMMENT ON COLUMN public.exercise_training_styles.notes IS 'Additional notes about using this exercise in this training style';

COMMENT ON TABLE public.exercise_muscles IS 'Many-to-many relationship defining which muscles are worked by each exercise and their roles';
COMMENT ON COLUMN public.exercise_muscles.muscle_role IS 'Role of muscle group in exercise - primary mover, secondary mover, or stabilizer';
COMMENT ON COLUMN public.exercise_muscles.activation_level IS 'Relative activation level from 1 (minimal) to 5 (maximal) for exercise programming';

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

COMMENT ON TABLE public.exercise_relationships IS 'Defines relationships between exercises for programming and progression recommendations';
COMMENT ON COLUMN public.exercise_relationships.relationship_type IS 'Type of relationship - variation, progression/regression, alternative, antagonist pair, or superset pairing';
COMMENT ON COLUMN public.exercise_relationships.notes IS 'Additional context about when to use this relationship (e.g., equipment substitution, injury modification)';

-- =============================================================================
-- WORKOUT PLANNING TABLES
-- =============================================================================

-- Plans table (workout plan templates)
CREATE TABLE IF NOT EXISTS public.plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
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
    -- Ensure unique versioning per user and plan name
    UNIQUE(user_id, name, version_number)
);

COMMENT ON TABLE public.plans IS 'Versioned workout plan templates that can be followed by users or shared publicly. Plans are immutable once created - modifications create new versions.';
COMMENT ON COLUMN public.plans.goal IS 'Primary training goal this plan targets (e.g., "strength", "hypertrophy", "weight_loss")';
COMMENT ON COLUMN public.plans.duration_weeks IS 'Planned duration in weeks before progression or plan change';
COMMENT ON COLUMN public.plans.days_per_week IS 'Intended training frequency per week';
COMMENT ON COLUMN public.plans.is_public IS 'Whether this plan can be discovered and used by other users';
COMMENT ON COLUMN public.plans.metadata IS 'Additional plan configuration like periodization, rest weeks, deload protocols';
COMMENT ON COLUMN public.plans.version_number IS 'Version number for this plan iteration (increments with each modification)';
COMMENT ON COLUMN public.plans.parent_plan_id IS 'References the original plan this version derives from (NULL for v1)';
COMMENT ON COLUMN public.plans.is_active IS 'Whether this is the current active version of the plan (only one version per plan name should be active)';

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

COMMENT ON TABLE public.plan_exercises IS 'Junction table defining exercises within workout plans and their programming parameters';
COMMENT ON COLUMN public.plan_exercises.day_of_week IS 'Day of week (1=Monday, 7=Sunday) when this exercise is scheduled';
COMMENT ON COLUMN public.plan_exercises.order_in_day IS 'Order of exercise within the workout session (1st, 2nd, 3rd, etc.)';
COMMENT ON COLUMN public.plan_exercises.target_reps IS 'Array of target rep ranges for each set (e.g., [8,10,12] for 3 sets)';
COMMENT ON COLUMN public.plan_exercises.rest_seconds IS 'Recommended rest period between sets in seconds';

-- =============================================================================
-- WORKOUT EXECUTION TABLES
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
-- AI TABLES
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

COMMENT ON TABLE public.conversations IS 'AI chat session boundaries and context for managing conversation history and state';
COMMENT ON COLUMN public.conversations.started_at IS 'When the conversation session began (first message timestamp)';
COMMENT ON COLUMN public.conversations.ended_at IS 'When the conversation session ended (null for ongoing conversations)';
COMMENT ON COLUMN public.conversations.context IS 'Session context like conversation summary, user goals, or AI personality state';

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

COMMENT ON TABLE public.memories IS 'AI semantic memory store with vector embeddings for personalized context retrieval';
COMMENT ON COLUMN public.memories.content IS 'Text content of the memory for semantic search and AI context';
COMMENT ON COLUMN public.memories.embedding IS 'Vector embedding of content for similarity search (3072 dimensions for gemini-embeddings-001)';
COMMENT ON COLUMN public.memories.memory_type IS 'Category of memory for filtering and importance weighting';
COMMENT ON COLUMN public.memories.importance_score IS 'Dynamic importance score from 0-1, may be updated based on relevance and recency';
COMMENT ON COLUMN public.memories.metadata IS 'Additional memory context like emotion, entities, or confidence scores';

-- =============================================================================
-- RLS POLICIES
-- =============================================================================

-- Enable RLS on core tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exercises ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.plan_exercises ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workout_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.memories ENABLE ROW LEVEL SECURITY;

-- Enable RLS on reference tables
ALTER TABLE public.movement_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.muscle_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.equipment_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.training_styles ENABLE ROW LEVEL SECURITY;

-- Enable RLS on junction tables
ALTER TABLE public.exercise_movement_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exercise_muscles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exercise_training_styles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exercise_relationships ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATED_AT MANAGEMENT
-- =============================================================================

-- Create triggers for all tables with updated_at columns
-- These automatically update the updated_at timestamp when any row is modified

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

-- =============================================================================
-- TRIGGER FOR AUTOMATIC PROFILE CREATION
-- =============================================================================

-- Create trigger on auth.users to automatically create profile entries
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();