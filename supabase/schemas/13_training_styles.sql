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