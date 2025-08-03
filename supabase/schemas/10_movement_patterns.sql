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