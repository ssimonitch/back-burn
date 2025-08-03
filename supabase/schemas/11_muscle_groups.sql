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