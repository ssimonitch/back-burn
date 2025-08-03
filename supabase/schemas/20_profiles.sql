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
CREATE TRIGGER on_auth_user_created
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