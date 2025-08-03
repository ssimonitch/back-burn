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